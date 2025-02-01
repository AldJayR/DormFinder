import re
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from encrypted_model_fields.fields import EncryptedCharField

import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException

def validate_ph_phone(value):
    """Validate Philippine mobile number using libphonenumber"""
    try:
        phone = phonenumbers.parse(value, "PH")
        if not phonenumbers.is_valid_number_for_region(phone, "PH"):
            raise ValidationError(
                _("Invalid Philippine mobile number format")
            )
    except NumberParseException:
        raise ValidationError(
            _("Invalid phone number format")
        )

def validate_neust_id(value):
    """Validate NEUST ID formats"""
    campus_pattern = r'^NEUST-\d{4}-\d{5}$'  
    numeric_pattern = r'^\d{8,10}$'
    
    if not (re.match(campus_pattern, value) or re.match(numeric_pattern, value)):
        raise ValidationError(_(
            "Invalid NEUST ID. Valid formats: "
            "(1) NEUST-YYYY-##### (e.g., NEUST-2023-00111) "
            "(2) Numeric ID (8-10 digits)"
        ))

class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = 'student', _('Student')
        DORM_OWNER = 'dorm_owner', _('Dorm Owner')
        ADMIN = 'admin', _('Admin')

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("Unique identifier for the user")
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        help_text=_("User role in the system"),
        db_index=True
    )
    phone = EncryptedCharField(
        max_length=15,
        unique=True,
        validators=[validate_ph_phone],
        help_text=_("PH mobile number (+639XXXXXXXXX)")
    )
    school_id_number = EncryptedCharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        validators=[validate_neust_id],
        help_text=_("NEUST student ID (e.g., NEUST-2023-12345)")
    )
    is_verified = models.BooleanField(
        default=False,
        help_text=_("Verified by admin (for dorm owners)"),
        db_index=True
    )

    first_name = None
    last_name = None

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_('The groups this user belongs to.'),
        related_name='custom_user_set',
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='custom_user_set',
        related_query_name='user',
    )

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ['-date_joined']
        constraints = [
            models.UniqueConstraint(
                fields=['phone'],
                name="unique_ph_phone"
            ),
            models.CheckConstraint(
                check=models.Q(
                    (models.Q(role='student') & models.Q(school_id_number__isnull=False)) |
                    models.Q(role__in=['dorm_owner', 'admin'])
                ),
                name="student_requires_neust_id"
            )
        ]

    def clean(self):
        """Custom validation rules"""
        super().clean()
        
        if self.role == self.Role.STUDENT and not self.school_id_number:
            raise ValidationError({
                'school_id_number': _("NEUST ID is required for students.")
            })
            
        if self.role == self.Role.DORM_OWNER and not self.is_verified:
            raise ValidationError({
                'is_verified': _("Dorm owners require admin verification.")
            })

    def __str__(self):
        return f"{self.username} ({self.role})"
