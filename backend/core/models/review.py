from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from .user import User
from .dorm import Dorm

class Review(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='reviews',
        limit_choices_to={'role': 'student'}
    )
    dorm = models.ForeignKey(
        Dorm, 
        on_delete=models.CASCADE, 
        related_name='reviews'
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1 (Poor) to 5 (Excellent)"
    )
    comment = models.TextField(
        blank=True,
        help_text="Optional detailed feedback"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'dorm'], 
                name="one_review_per_user_per_dorm"
            )
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user}'s Review - {self.rating}★"