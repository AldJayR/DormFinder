from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import exceptions
from django.utils.translation import gettext_lazy as _

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        
        if not hasattr(self.user, 'profile'):
            raise exceptions.AuthenticationFailed(
                _('User profile not configured properly'),
                code='invalid_profile'
            )
            
        refresh = self.get_token(self.user)
        
        data.update({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': self.user.id,
                'email': self.user.email,
                'role': self.user.role,
                'is_staff': self.user.profile.is_staff,
                'is_superuser': self.user.profile.is_superuser
            }
        })
        return data
