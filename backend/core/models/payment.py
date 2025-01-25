from django.db import models
from .booking import Booking
from django.core.validators import MinValueValidator


class Payment(models.Model):
    METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('gcash', 'GCash'),
        ('bank_transfer', 'Bank Transfer'),
    )

    booking = models.OneToOneField(
        Booking, 
        on_delete=models.CASCADE, 
        related_name='payment'
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    method = models.CharField(
        max_length=20, 
        choices=METHOD_CHOICES, 
        default='cash'
    )
    reference_number = models.CharField(
        max_length=100, 
        blank=True,
        help_text="GCash transaction ID or bank reference"
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Manually verified by admin for cash payments"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Payment Record"
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment #{self.id} - ₱{self.amount}"