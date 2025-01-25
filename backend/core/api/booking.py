from rest_framework import viewsets, status
from rest_framework.response import Response
from core.models import Booking
from core.serializers import booking_serializers
from core.permissions import IsStudent

class BookingViewSet(viewsets.ModelViewSet):
    """PH academic calendar-aware bookings"""
    serializer_class = booking_serializers
    permission_classes = [IsStudent]

    def get_queryset(self):
        """Student-specific PH bookings"""
        return Booking.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """PH-style booking validation"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        if self._has_booking_conflict(serializer.validated_data):
            return Response(
                {'detail': 'Date conflict with existing booking'},
                status=status.HTTP_409_CONFLICT
            )
            
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _has_booking_conflict(self, data):
        """PH academic calendar conflict check"""
        return Booking.objects.filter(
            user=self.request.user,
            dorm=data['dorm'],
            move_in_date__lte=data['move_out_date'],
            move_out_date__gte=data['move_in_date']
        ).exists()