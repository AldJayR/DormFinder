from rest_framework import serializers
from ..models import User

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'role', 'phone', 'school_id_number']
        extra_kwargs = {
            'phone': {'write_only': True},
            'school_id_number': {'write_only': True}
        }

    def validate(self, data):
        # PH-specific validation
        if data['role'] == 'student' and not data.get('school_id_number'):
            raise serializers.ValidationError("NEUST ID is required for students.")
        return data

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'role', 'is_verified']
        read_only_fields = ['is_verified']

class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'