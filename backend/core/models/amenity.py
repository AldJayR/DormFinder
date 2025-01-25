from django.db import models

class Amenity(models.Model):
    name = models.CharField(
        max_length=100, 
        unique=True,
        help_text="Common PH dorm amenities (e.g., WiFi, Laundry Area)"
    )
    icon = models.CharField(
        max_length=50, 
        blank=True,
        help_text="FontAwesome icon class (e.g., 'fa-wifi')"
    )

    class Meta:
        verbose_name_plural = "Amenities"
        ordering = ['name']

    def __str__(self):
        return self.name