from django.db import models
from django.utils.translation import gettext_lazy as _  
from .user import User
from .dorm import Dorm


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending Approval')
        CONFIRMED = 'confirmed', _('Confirmed')
        CANCELED = 'canceled', _('Canceled')
        COMPLETED = 'completed', _('Completed')

    STATUS_TRANSITIONS = {
        Status.PENDING: [Status.CONFIRMED, Status.CANCELED],
        Status.CONFIRMED: [Status.COMPLETED, Status.CANCELED],
        Status.COMPLETED: [],
        Status.CANCELED: [],
    }

    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='bookings',
        limit_choices_to={'role': 'student'}
    )
    dorm = models.ForeignKey(
        Dorm, 
        on_delete=models.CASCADE, 
        related_name='bookings'
    )
    move_in_date = models.DateField(help_text="Follows PH academic calendar")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Booking")
        verbose_name_plural = _("Bookings")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['move_in_date']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(move_in_date__gt=models.F('created_at')),
                name='move_in_after_creation'
            )
        ]

    def __str__(self):
        return _(f"Booking #{self.id} - {self.dorm.name}")

    def clean(self):
        """Validate status transitions and move-in dates"""
        from django.utils import timezone
        from django.core.exceptions import ValidationError
        
        # Check status transitions
        if self.pk:
            original = Booking.objects.get(pk=self.pk)
            if original.status != self.status:
                allowed_transitions = self.STATUS_TRANSITIONS.get(original.status, [])
                if self.status not in allowed_transitions:
                    raise ValidationError({
                        'status': _("Invalid transition from %(original)s to %(new)s") % {
                            'original': original.get_status_display(),
                            'new': self.get_status_display()
                        }
                    })

        # Validate move-in date
        if self.move_in_date < timezone.localtime(timezone.now()).date():
            raise ValidationError({
                'move_in_date': _("Move-in date cannot be in the past")
            })

    def save(self, *args, **kwargs):
        """Ensure validation is run on every save"""
        self.full_clean()
        super().save(*args, **kwargs)
