from django.db import models
from django.core.validators import MinValueValidator
from .user import User
from .amenity import Amenity

class Dorm(models.Model):
    owner = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='dorms',
        limit_choices_to={'role': 'dorm_owner'}
    )
    name = models.CharField(max_length=200)
    address = models.TextField()
    monthly_rate = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(1500)],
        help_text="Monthly rent in PHP"
    )
    distance_from_school = models.CharField(
        max_length=50, 
        default="5-minute walk",
        help_text="Walking distance from NEUST campus"
    )
    amenities = models.ManyToManyField(
        Amenity, 
        related_name='dorms',
        blank=True
    )
    rules = models.TextField(
        blank=True, 
        help_text="Curfew time, visitor policies, etc."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['monthly_rate']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = "Dormitory"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} (₱{self.monthly_rate}/month)"