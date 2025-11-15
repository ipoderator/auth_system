from django.contrib import admin
from .models import Resource, Action, Permission, Role, RolePermission, UserRole


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    """Admin interface for Resource."""
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at',)


@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    """Admin interface for Action."""
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at',)


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    """Admin interface for Permission."""
    list_display = ('resource', 'action', 'created_at')
    list_filter = ('resource', 'action', 'created_at')
    search_fields = ('resource__name', 'action__name')


class RolePermissionInline(admin.TabularInline):
    """Inline admin for RolePermission."""
    model = RolePermission
    extra = 1


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Admin interface for Role."""
    list_display = ('name', 'description', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at', 'updated_at')
    inlines = [RolePermissionInline]
    filter_horizontal = ('permissions',)


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """Admin interface for UserRole."""
    list_display = ('user', 'role', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('user__email', 'role__name')

