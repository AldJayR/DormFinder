from rest_framework import serializers
from ..models import Review
from rest_framework.validators import UniqueTogetherValidator

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'user', 'dorm', 'rating', 'comment', 'created_at']
        read_only_fields = ['user', 'created_at']
        validators = [
            UniqueTogetherValidator(
                queryset=Review.objects.all(),
                fields=['user', 'dorm'],
                message="You've already reviewed this dorm."
            )
        ]

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5 stars.")
        return value