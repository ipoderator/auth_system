from rest_framework import permissions
from .models import UserRole


class HasResourcePermission(permissions.BasePermission):
    """
    Custom permission to check if user has access to a specific resource and action.
    Usage: permission_classes = [HasResourcePermission(resource='products', action='read')]
    """
    
    def __init__(self, resource=None, action=None):
        self.resource = resource
        self.action = action
    
    def has_permission(self, request, view):
        """Check if user has permission for the resource and action."""
        # Allow unauthenticated users to be handled by IsAuthenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        
        # Get resource and action from view or use defaults
        resource = getattr(view, 'resource_name', None) or self.resource
        action = getattr(view, 'action_name', None) or self.action
        
        # Map DRF actions to our action names
        if not action:
            action_mapping = {
                'list': 'list',
                'retrieve': 'read',
                'create': 'create',
                'update': 'update',
                'partial_update': 'update',
                'destroy': 'delete',
            }
            action = action_mapping.get(view.action, view.action)
        
        if not resource:
            return False
        
        # Check if user has any role with the required permission
        user_roles = UserRole.objects.filter(
            user=request.user,
            role__permissions__resource__name=resource,
            role__permissions__action__name=action
        ).exists()
        
        return user_roles


def check_resource_permission(user, resource_name, action_name):
    """
    Helper function to check if user has permission for a resource and action.
    Returns True if user has permission, False otherwise.
    """
    if not user or not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    return UserRole.objects.filter(
        user=user,
        role__permissions__resource__name=resource_name,
        role__permissions__action__name=action_name
    ).exists()


class IsAdmin(permissions.BasePermission):
    """Permission class to check if user has Admin role."""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        return UserRole.objects.filter(
            user=request.user,
            role__name='Admin'
        ).exists()

