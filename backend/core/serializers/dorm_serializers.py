from rest_framework import serializers
from ..models import Dorm
from .amenity_serializers import AmenitySerializer

class DormSerializer(serializers.ModelSerializer):
    amenities = AmenitySerializer(many=True, read_only=True)
    owner = serializers.StringRelatedField(source='owner.username')  # Show owner's username
    
    class Meta:
        model = Dorm
        fields = [
            'id', 'name', 'address', 'monthly_rate', 'distance_from_school',
            'amenities', 'rules', 'owner', 'created_at'
        ]
        read_only_fields = ['owner', 'created_at']

    def create(self, validated_data):
        # Auto-set owner to current user
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)