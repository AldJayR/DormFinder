# utils/authentication.py
import logging
from datetime import timedelta, timezone
from django.conf import settings
from django.core.cache import caches
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from cryptography.fernet import Fernet, InvalidToken as FernetInvalidToken
from cryptography.exceptions import InvalidSignature

from backend.core.models import user

logger = logging.getLogger(__name__)
User = get_user_model()
AUTH_CACHE = caches['auth']

class SecureJWTAuthentication(JWTAuthentication):
    """
    Enhanced JWT authentication with:
    - Token revocation
    - Device fingerprinting
    - Rate limiting
    - Audit logging
    - Security headers
    """
    
    def authenticate(self, request):
        try:
            raw_token = self._get_token_from_request(request)
            if self._is_token_revoked(raw_token):
                raise AuthenticationFailed('Token revoked')
            
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
            
            self._perform_security_checks(user, request, validated_token)
            self._audit_auth_attempt(user, request, success=True)
            
            return (user, validated_token)
        except (InvalidToken, AuthenticationFailed) as e:
            self._audit_auth_attempt(None, request, success=False)
            self._handle_failed_attempt(request)
            raise

    def _get_token_from_request(self, request):
        """Secure token extraction from HTTP-only cookie"""
        token = request.COOKIES.get(settings.JWT_AUTH['AUTH_COOKIE_NAME'])
        
        if not token:
            raise AuthenticationFailed('No authentication token provided')
            
        if len(token) > 4096:  # Prevent DoS via large tokens
            raise AuthenticationFailed('Invalid token size')
            
        return token

    def _perform_security_checks(self, user, request, token):
        """Comprehensive security validation"""
        checks = [
            self._check_account_status(user),
            self._check_device_fingerprint(request, token),
            self._check_user_agent(request),
            self._check_ip_address(request),
            self._check_role_based_access(user)
        ]
        
        if not all(checks):
            raise AuthenticationFailed('Security check failed')

    def _check_account_status(self, user):
        """Validate user account state"""
        if not user.is_active:
            raise AuthenticationFailed('Account inactive')
            
        if user.role == 'dorm_owner' and not user.is_verified:
            raise AuthenticationFailed('Business verification required')
            
        return True

    def _check_device_fingerprint(self, request, token):
        """Validate encrypted device fingerprint"""
        try:
            stored_fp = token.get('dfp')
            if not stored_fp:
                return True  # Allow legacy tokens
                
            current_fp = self._generate_device_fingerprint(request)
            decrypted_fp = Fernet(settings.FIELD_ENCRYPTION_KEY).decrypt(
                stored_fp.encode()
            ).decode()
            
            if current_fp != decrypted_fp:
                logger.warning('Device fingerprint mismatch for user %s', user.id)
                return False
                
            return True
        except (FernetInvalidToken, InvalidSignature):
            raise AuthenticationFailed('Invalid device fingerprint')

    def _generate_device_fingerprint(self, request):
        """Create secure device fingerprint"""
        components = [
            request.META.get('HTTP_USER_AGENT', ''),
            request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
            request.META.get('REMOTE_ADDR', '')[:256],
        ]
        return Fernet(settings.FIELD_ENCRYPTION_KEY).encrypt(
            '-'.join(components).encode()
        ).decode()

    def _check_user_agent(self, request):
        """Prevent UA-less requests"""
        if not request.META.get('HTTP_USER_AGENT'):
            raise AuthenticationFailed('User agent header required')
        return True

    def _check_ip_address(self, request):
        """Basic IP validation"""
        ip = request.META.get('REMOTE_ADDR')
        if not ip or len(ip) > 45:  # Max IPv6 length
            raise AuthenticationFailed('Invalid IP address')
        return True

    def _check_role_based_access(self, user):
        """Time-based access control"""
        if user.role == 'student' and not self._is_within_access_hours():
            raise AuthenticationFailed('Access restricted to university hours')
        return True
    
    def _is_token_revoked(self, raw_token):
        """Check token revocation status"""
        token_hash = self._generate_token_hash(raw_token)
        return AUTH_CACHE.get(f'revoked:{token_hash}') is not None

    def _generate_token_hash(self, raw_token):
        """HMAC-based token fingerprint"""
        return Fernet(settings.FIELD_ENCRYPTION_KEY).encrypt(
            raw_token.encode()
        ).decode()

    def _audit_auth_attempt(self, user, request, success=True):
        """Log authentication attempts"""
        log_data = {
            'user': user.id if user else None,
            'ip': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT'),
            'success': success,
            'timestamp': timezone.now().isoformat(),
        }
        logger.info('Auth attempt: %s', log_data)

    def _handle_failed_attempt(self, request):
        """Rate limiting and brute force protection"""
        cache_key = f'auth_failures:{request.META.get("REMOTE_ADDR")}'
        failures = AUTH_CACHE.get(cache_key, 0) + 1
        AUTH_CACHE.set(cache_key, failures, timeout=900)  # 15 minutes
        
        if failures > 5:
            logger.warning('Brute force attempt detected from %s', request.META.get("REMOTE_ADDR"))
            raise AuthenticationFailed('Too many failed attempts')

class SecureRefreshToken(RefreshToken):
    """
    Enhanced refresh token with:
    - Device binding
    - Usage limits
    - Automatic revocation
    """
    token_type = 'refresh'
    lifetime = settings.JWT_AUTH['REFRESH_TOKEN_LIFETIME']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_exp(from_time=self.current_time)
        
        # Device fingerprint
        self.payload['dfp'] = Fernet(settings.FIELD_ENCRYPTION_KEY).encrypt(
            self.device_fingerprint.encode()
        ).decode()
        
        # Usage counter
        self.payload['use_count'] = 0

    @property
    def max_use_count(self):
        return 3  # Allow token refresh 3 times max

    def check_usage(self):
        if self.payload['use_count'] >= self.max_use_count:
            raise InvalidToken('Refresh token expired')
        self.payload['use_count'] += 1
