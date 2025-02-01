from rest_framework import permissions
from django.utils.translation import gettext_lazy as _

class IsBookingOwner(permissions.BasePermission):
    message = _("You must be the owner of this booking to perform this action")
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user

class IsDormOwner(permissions.BasePermission):
    message = _("You must be the owner of this dorm to perform this action")
    
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user

class IsAdminOrReadOnly(permissions.BasePermission):
    message = _("This action requires administrator privileges")
    
    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS or
            request.user and
            request.user.is_authenticated and
            request.user.is_staff
        )


class IsStudent(permissions.BasePermission):
    message = _("Only students are allowed to perform this action.")

    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, 'role', None) == 'student'