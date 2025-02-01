from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.models import Booking
from core.serializers.booking_serializers import BookingSerializer
from core.permissions import IsStudent

class BookingViewSet(viewsets.ModelViewSet):
    """
    Handles student dorm bookings with conflict checking and transaction safety
    """
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated, IsStudent]

    def get_queryset(self):
        """Return bookings for current student with related data"""
        return Booking.objects.filter(user=self.request.user).select_related('dorm', 'user')

    def create(self, request, *args, **kwargs):
        """Atomic booking creation with conflict checking"""
        with transaction.atomic():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            if self._has_booking_conflict(serializer.validated_data):
                return Response(
                    {'errors': {'dates': ['Conflicts with existing booking']}},
                    status=status.HTTP_409_CONFLICT
                )

            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def _has_booking_conflict(self, data):
        """Check for overlapping bookings using database-level locking"""
        return Booking.objects.select_for_update().filter(
            user=self.request.user,
            dorm=data['dorm'],
            move_in_date__lte=data['move_out_date'],
            move_out_date__gte=data['move_in_date']
        ).exists()