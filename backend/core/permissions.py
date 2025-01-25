from rest_framework import permissions

class BaseRolePermission(permissions.BasePermission):
    role = None
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == self.role

class IsStudent(BaseRolePermission):
    role = 'student'

class IsDormOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user

class IsAdmin(BaseRolePermission):
    role = 'admin'