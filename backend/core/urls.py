from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from .api import auth, dorm, booking
from forum.views import PostViewSet, CommentViewSet

# Main API router
router = DefaultRouter(trailing_slash=False)
router.register(r'dorms', dorm.DormViewSet, basename='dorm')
router.register(r'bookings', booking.BookingViewSet, basename='booking')

# Nested routers for forum features
forum_router = routers.NestedSimpleRouter(router, r'dorms', lookup='dorm')
forum_router.register(r'posts', PostViewSet, basename='dorm-posts')

post_router = routers.NestedSimpleRouter(forum_router, r'posts', lookup='post')
post_router.register(r'comments', CommentViewSet, basename='post-comments')

urlpatterns = [
    # Authentication endpoints
    path('api/auth/login/', auth.SecureTokenObtainPairView.as_view(), name='login'),
    path('api/auth/register/', auth.RegisterView.as_view(), name='register'),
    path('api/auth/logout/', auth.logout_view, name='logout'),
    path('api/auth/refresh/', auth.SecureTokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/me/', auth.UserDetailView.as_view(), name='user-detail'),
    
    # Include all router URLs
    path('api/', include(router.urls)),
    path('api/', include(forum_router.urls)),
    path('api/', include(post_router.urls)),
    
    # Browsable API auth
    path('api/auth/', include('rest_framework.urls', namespace='rest_framework')),
]