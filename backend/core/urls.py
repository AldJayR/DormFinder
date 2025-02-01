from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import auth, dorm, booking
from rest_framework.schemas import get_schema_view

# API Versioning
API_VERSION = 'v1'

# Schema View
schema_view = get_schema_view(
    title="Dormfinder API",
    description="API for dormitory management system",
    version=API_VERSION,
)

# Main API router
router = DefaultRouter(trailing_slash=True)  # Enforce consistency
router.register(r'dorms', dorm.DormViewSet, basename='dorm')
router.register(r'bookings', booking.BookingViewSet, basename='booking')

urlpatterns = [
    # API Documentation
    path(f'api/{API_VERSION}/schema/', schema_view, name='api-schema'),
    
    # Authentication endpoints
    path(f'api/{API_VERSION}/auth/login/', auth.SecureTokenObtainPairView.as_view(), name='login'),
    path(f'api/{API_VERSION}/auth/register/', auth.RegisterView.as_view(), name='register'),
    path(f'api/{API_VERSION}/auth/logout/', auth.logout_view, name='logout'),
    path(f'api/{API_VERSION}/auth/refresh/', auth.SecureTokenRefreshView.as_view(), name='token_refresh'),
    path(f'api/{API_VERSION}/auth/me/', auth.UserDetailView.as_view(), name='user-detail'),
    
    # Include main router URLs
    path(f'api/{API_VERSION}/', include(router.urls)),
    
    # Browsable API auth (dev only)
    path(f'api/{API_VERSION}/auth/', include('rest_framework.urls', namespace='rest_framework')),
]
