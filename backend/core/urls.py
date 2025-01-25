from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import auth, dorm, booking

# Main API router
router = DefaultRouter(trailing_slash=False)
router.register(r'dorms', dorm.DormViewSet, basename='dorm')
router.register(r'bookings', booking.BookingViewSet, basename='booking')

urlpatterns = [
    # Authentication endpoints
    path('api/auth/login/', auth.SecureTokenObtainPairView.as_view(), name='login'),
    path('api/auth/register/', auth.RegisterView.as_view(), name='register'),
    path('api/auth/logout/', auth.logout_view, name='logout'),
    path('api/auth/refresh/', auth.SecureTokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/me/', auth.UserDetailView.as_view(), name='user-detail'),
    
    # Include main router URLs
    path('api/', include(router.urls)),
    
    # Browsable API auth
    path('api/auth/', include('rest_framework.urls', namespace='rest_framework')),
]