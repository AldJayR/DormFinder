import logging
import hashlib
from django.conf import settings
from django.core.cache import caches
from django.utils import timezone
from django.middleware.csrf import get_token
from rest_framework import generics, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework.generics import RetrieveAPIView
from core.models import User
from core.serializers import CustomTokenObtainPairSerializer
from core.serializers.user_serializers import UserProfileSerializer

logger = logging.getLogger(__name__)
AUTH_CACHE = caches[settings.JWT_AUTH.get('REVOCATION_CACHE', 'default')]

def _token_hash(raw_token):
    """Generate secure token hash for revocation list"""
    return hashlib.sha256(
        f"{settings.SECRET_KEY}{raw_token}".encode()
    ).hexdigest()

class UserDetailView(RetrieveAPIView):
    """
    Retrieve current authenticated user details
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    def get_object(self):
        return self.request.user

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # Add security headers
        response.headers.update({
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY'
        })
        return response

class SecureTokenMixin:
    def _set_secure_cookies(self, response):
        """Set secure HTTP-only cookies with JWT tokens"""
        if response.status_code == status.HTTP_200_OK:
            # Set access token cookie
            response.set_cookie(
                key=settings.JWT_AUTH['ACCESS_COOKIE_NAME'],
                value=response.data['access'],
                httponly=True,
                secure=settings.JWT_AUTH['COOKIE_SECURE'],
                samesite=settings.JWT_AUTH['COOKIE_SAMESITE'],
                max_age=settings.JWT_AUTH['ACCESS_TOKEN_LIFETIME'].total_seconds(),
                path=settings.JWT_AUTH.get('COOKIE_PATH', '/'),
                domain=settings.JWT_AUTH.get('COOKIE_DOMAIN')
            )
            
            # Set refresh token cookie if present
            if 'refresh' in response.data:
                response.set_cookie(
                    key=settings.JWT_AUTH['REFRESH_COOKIE_NAME'],
                    value=response.data['refresh'],
                    httponly=True,
                    secure=settings.JWT_AUTH['COOKIE_SECURE'],
                    samesite=settings.JWT_AUTH['COOKIE_SAMESITE'],
                    max_age=settings.JWT_AUTH['REFRESH_TOKEN_LIFETIME'].total_seconds(),
                    path=settings.JWT_AUTH.get('COOKIE_PATH', '/'),
                    domain=settings.JWT_AUTH.get('COOKIE_DOMAIN')
                )
            
            # Remove tokens from response body
            response.delete('access')
            response.delete('refresh')

    def _get_client_ip(self, request):
        """Get client IP with proxy support"""
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR')

class SecureTokenObtainPairView(SecureTokenMixin, TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        self._set_secure_cookies(response)
        response['X-CSRFToken'] = get_token(request)
        
        if response.status_code == status.HTTP_200_OK:
            try:
                user = User.objects.get(username=request.data['username'])
                user.last_login = timezone.now()
                user.save(update_fields=['last_login'])
                logger.info(
                    f"Successful login: {user.username} "
                    f"from {self._get_client_ip(request)} "
                    f"via {request.META.get('HTTP_USER_AGENT', 'Unknown')}"
                )
            except User.DoesNotExist:
                logger.error("User login succeeded but not found in database")
        else:
            logger.warning(
                f"Failed login attempt: {request.data.get('username', 'Unknown')} "
                f"from {self._get_client_ip(request)}"
            )
        
        return response

class SecureTokenRefreshView(SecureTokenMixin, TokenRefreshView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        self._set_secure_cookies(response)
        response['X-CSRFToken'] = get_token(request)
        return response

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'registration'

    def perform_create(self, serializer):
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError
        
        password = serializer.validated_data.get('password')
        try:
            validate_password(password)
        except ValidationError as e:
            raise serializers.ValidationError({'password': e.messages})

        user = serializer.save(role='student')
        self._perform_post_registration_checks(user)
        
        logger.info(
            f"New registration: {user.username} "
            f"from IP {self._get_client_ip(self.request)}"
        )

    def _perform_post_registration_checks(self, user):
        if user.role == 'student':
            if not user.school_id_number:
                raise serializers.ValidationError({
                    'school_id_number': 'NEUST ID is required for student registration'
                })
            if not user.school_id_number.startswith('NEUST-'):
                raise serializers.ValidationError({
                    'school_id_number': 'Invalid NEUST ID format.'
                })

    def _get_client_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR')

@api_view(['POST'])
def logout_view(request):
    response = Response({'detail': 'Successfully logged out'}, status=status.HTTP_200_OK)
    
    # Revoke tokens
    if hasattr(request, 'auth'):
        try:
            raw_token = request.auth.token.decode()
            token_hash = _token_hash(raw_token)
            timeout = settings.JWT_AUTH['ACCESS_TOKEN_LIFETIME'].total_seconds()
            AUTH_CACHE.set(f'revoked:{token_hash}', True, timeout=timeout)
        except Exception as e:
            logger.error(f"Token revocation error: {str(e)}", exc_info=True)
    
    # Clear cookies
    for cookie_name in [settings.JWT_AUTH['ACCESS_COOKIE_NAME'],
                        settings.JWT_AUTH.get('REFRESH_COOKIE_NAME')]:
        if cookie_name:
            response.delete_cookie(
                cookie_name,
                path=settings.JWT_AUTH.get('COOKIE_PATH', '/'),
                domain=settings.JWT_AUTH.get('COOKIE_DOMAIN')
            )
    
    # Maintain CSRF for React
    response['X-CSRFToken'] = get_token(request)
    
    # Security headers
    response.headers.update({
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'Content-Security-Policy': "default-src 'self'",
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    })
    
    logger.info(f"User logout: {request.user.username[:3]}***")
    return response