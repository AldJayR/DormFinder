from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from core.models import Dorm
from core.serializers import dorm_serializers
from core.permissions import IsDormOwner

class DormViewSet(ModelViewSet):
    serializer_class = dorm_serializers.DormSerializer
    permission_classes = [IsDormOwner]
    filterset_fields = ['monthly_rate', 'distance_from_school']
    ordering_fields = ['created_at', 'monthly_rate']

    def get_queryset(self):
        """Filter queryset based on PH location preferences"""
        queryset = Dorm.objects.filter(is_approved=True)
        
        # PH-specific distance filtering
        if 'max_walk_time' in self.request.query_params:
            return queryset.filter(
                distance_from_school__lte=self._parse_walk_time()
            )
        return queryset

    def _parse_walk_time(self):
        """Convert PH-style walk time to minutes (e.g., '5-minute walk' → 5)"""
        try:
            return int(self.request.query_params['max_walk_time'].split('-')[0])
        except (ValueError, IndexError):
            return 10

    @action(detail=True, methods=['post'], url_path='ph-mark-verified')
    def mark_verified(self, request, pk=None):
        """PH-specific dorm verification endpoint"""
        dorm = self.get_object()
        dorm.ph_verified = True
        dorm.save()
        return Response({'status': 'NEUST Verified dorm'})