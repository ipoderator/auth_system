from django.db import models
from django.conf import settings


class Resource(models.Model):
    """Resource model - represents a business object/resource."""

    name = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name='Resource name'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Description'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created at'
    )

    class Meta:
        verbose_name = 'Resource'
        verbose_name_plural = 'Resources'
        db_table = 'resources'
        ordering = ['name']

    def __str__(self):
        return self.name


class Action(models.Model):
    """Action model - represents actions on resources."""

    name = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name='Action name'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Description'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created at'
    )

    class Meta:
        verbose_name = 'Action'
        verbose_name_plural = 'Actions'
        db_table = 'actions'
        ordering = ['name']

    def __str__(self):
        return self.name


class Permission(models.Model):
    """Permission model - combination of Resource and Action."""

    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name='permissions',
        verbose_name='Resource'
    )
    action = models.ForeignKey(
        Action,
        on_delete=models.CASCADE,
        related_name='permissions',
        verbose_name='Action'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created at'
    )

    class Meta:
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'
        db_table = 'permissions'
        unique_together = [['resource', 'action']]
        ordering = ['resource', 'action']

    def __str__(self):
        return f"{self.resource.name}.{self.action.name}"

    @classmethod
    def get_or_create_permission(cls, resource_name, action_name):
        """Get or create a permission by resource and action names."""
        resource, _ = Resource.objects.get_or_create(name=resource_name)
        action, _ = Action.objects.get_or_create(name=action_name)
        permission, created = cls.objects.get_or_create(
            resource=resource,
            action=action
        )
        return permission, created


class Role(models.Model):
    """Role model - represents a role with multiple permissions."""

    name = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name='Role name'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Description'
    )
    permissions = models.ManyToManyField(
        Permission,
        through='RolePermission',
        related_name='roles',
        verbose_name='Permissions'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created at'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated at'
    )

    class Meta:
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'
        db_table = 'roles'
        ordering = ['name']

    def __str__(self):
        return self.name

    def has_permission(self, resource_name, action_name):
        """Check if role has a specific permission."""
        return self.permissions.filter(
            resource__name=resource_name,
            action__name=action_name
        ).exists()


class RolePermission(models.Model):
    """Intermediate model for Role-Permission relationship."""

    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='role_permissions',
        verbose_name='Role'
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name='role_permissions',
        verbose_name='Permission'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created at'
    )

    class Meta:
        verbose_name = 'Role Permission'
        verbose_name_plural = 'Role Permissions'
        db_table = 'role_permissions'
        unique_together = [['role', 'permission']]

    def __str__(self):
        return f"{self.role.name} - {self.permission}"


class UserRole(models.Model):
    """Model for assigning roles to users."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_roles',
        verbose_name='User'
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='user_roles',
        verbose_name='Role'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created at'
    )

    class Meta:
        verbose_name = 'User Role'
        verbose_name_plural = 'User Roles'
        db_table = 'user_roles'
        unique_together = [['user', 'role']]
        ordering = ['user', 'role']

    def __str__(self):
        return f"{self.user.email} - {self.role.name}"
