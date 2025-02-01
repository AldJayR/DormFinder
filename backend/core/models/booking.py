import logging
from django.db import models
from django.utils.translation import gettext_lazy as _
from .user import User
from .dorm import Dorm

logger = logging.getLogger(__name__)


class Booking(models.Model):
    _status_change_notification_sent = False  # Track if notification was sent
    
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
    move_in_date = models.DateField(help_text="Follows academic calendar", db_index=True)
    move_out_date = models.DateField(db_index=True)
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
            models.Index(fields=['user', 'status'], name='booking_user_status_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(move_in_date__gt=models.F('created_at')),
                name='move_in_after_creation'
            ),
            models.CheckConstraint(
                check=models.Q(move_out_date__gt=models.F('move_in_date')),
                name='move_out_after_move_in'
            ),
            models.UniqueConstraint(
                fields=['user', 'dorm', 'move_in_date'],
                name='unique_user_dorm_movein'
            )
        ]

    def __str__(self):
        return _("Booking #{id} - {name}").format(
            id=self.id,
            name=self.dorm.name
        )

    def clean(self):
        """Validate status transitions and move-in dates with row locking"""
        from django.utils import timezone
        from django.core.exceptions import ValidationError
        
        if self.pk:
            # Lock row for concurrent updates
            original = Booking.objects.select_for_update().get(pk=self.pk)
            if original.status != self.status:
                allowed_transitions = self.STATUS_TRANSITIONS.get(original.status, [])
                if self.status not in allowed_transitions:
                    raise ValidationError({
                        'status': _("Invalid transition from %(original)s to %(new)s") % {
                            'original': original.get_status_display(),
                            'new': self.get_status_display()
                        }
                    })

        # Always validate move-in date regardless of status changes
        if self.move_in_date < timezone.localtime(timezone.now()).date():
            raise ValidationError({
                'move_in_date': _("Move-in date cannot be in the past")
            })
            
        # Validate dorm availability
        if not self.dorm.is_available_for(self.move_in_date, self.move_out_date):
            raise ValidationError({
                'dorm': _("This dorm is not available for the selected dates")
            })

    def save(self, *args, **kwargs):
        """Atomic save with concurrency controls and dorm locking"""
        from django.db import transaction
        
        with transaction.atomic():
            self.full_clean()
            super().save(*args, **kwargs)
            
            # Lock dorm row during availability update
            dorm = Dorm.objects.select_for_update().get(pk=self.dorm_id)
            dorm.update_availability_cache()
            
            if self.pk:
                original = Booking.objects.get(pk=self.pk)
                if original.status != self.status:
                    logger.info(
                        "Booking %d status changed: %s → %s",
                        self.id,
                        original.status,
                        self.status
                    )
