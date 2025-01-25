from rest_framework import serializers
from ..models import Booking
from django.utils import timezone

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'user', 'dorm', 'move_in_date', 'move_out_date', 'status']
        read_only_fields = ['user', 'status']

    def validate(self, data):
        # PH academic calendar alignment
        if data['move_in_date'] < timezone.now().date():
            raise serializers.ValidationError("Move-in date cannot be in the past.")
        
        if data['move_out_date'] <= data['move_in_date']:
            raise serializers.ValidationError("Move-out must be after move-in date.")
        
        # Check dorm availability
        existing_bookings = Booking.objects.filter(
            dorm=data['dorm'],
            move_out_date__gt=data['move_in_date'],
            move_in_date__lt=data['move_out_date']
        ).exists()
        
        if existing_bookings:
            raise serializers.ValidationError("Dorm is already booked for these dates.")
        
        return data