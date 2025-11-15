from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.authorization.models import (
    Resource, Action, Permission, Role, RolePermission, UserRole
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Initialize test data for authorization system'

    def handle(self, *args, **options):
        self.stdout.write('Creating test data...')
        
        # Create Resources
        self.stdout.write('Creating resources...')
        resources = {}
        resource_names = ['products', 'orders', 'reports', 'users']
        for name in resource_names:
            resource, created = Resource.objects.get_or_create(
                name=name,
                defaults={'description': f'{name.capitalize()} resource'}
            )
            resources[name] = resource
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created resource: {name}'))
        
        # Create Actions
        self.stdout.write('Creating actions...')
        actions = {}
        action_names = ['create', 'read', 'update', 'delete', 'list']
        for name in action_names:
            action, created = Action.objects.get_or_create(
                name=name,
                defaults={'description': f'{name.capitalize()} action'}
            )
            actions[name] = action
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created action: {name}'))
        
        # Create Permissions
        self.stdout.write('Creating permissions...')
        permissions = {}
        for resource_name, resource in resources.items():
            for action_name, action in actions.items():
                permission, created = Permission.objects.get_or_create(
                    resource=resource,
                    action=action
                )
                key = f'{resource_name}.{action_name}'
                permissions[key] = permission
                if created:
                    self.stdout.write(self.style.SUCCESS(f'  Created permission: {key}'))
        
        # Create Roles
        self.stdout.write('Creating roles...')
        
        # Admin role - all permissions
        admin_role, created = Role.objects.get_or_create(
            name='Admin',
            defaults={'description': 'Administrator with all permissions'}
        )
        if created:
            for permission in permissions.values():
                RolePermission.objects.create(role=admin_role, permission=permission)
            self.stdout.write(self.style.SUCCESS('  Created role: Admin'))
        
        # Manager role - products.*, orders.read, orders.list
        manager_role, created = Role.objects.get_or_create(
            name='Manager',
            defaults={'description': 'Manager with products and orders read permissions'}
        )
        if created:
            manager_permissions = [
                'products.create', 'products.read', 'products.update', 'products.delete', 'products.list',
                'orders.read', 'orders.list'
            ]
            for perm_key in manager_permissions:
                if perm_key in permissions:
                    RolePermission.objects.create(role=manager_role, permission=permissions[perm_key])
            self.stdout.write(self.style.SUCCESS('  Created role: Manager'))
        
        # User role - products.read, products.list, orders.create
        user_role, created = Role.objects.get_or_create(
            name='User',
            defaults={'description': 'Regular user with limited permissions'}
        )
        if created:
            user_permissions = ['products.read', 'products.list', 'orders.create']
            for perm_key in user_permissions:
                if perm_key in permissions:
                    RolePermission.objects.create(role=user_role, permission=permissions[perm_key])
            self.stdout.write(self.style.SUCCESS('  Created role: User'))
        
        # Guest role - products.list
        guest_role, created = Role.objects.get_or_create(
            name='Guest',
            defaults={'description': 'Guest with minimal permissions'}
        )
        if created:
            guest_permissions = ['products.list']
            for perm_key in guest_permissions:
                if perm_key in permissions:
                    RolePermission.objects.create(role=guest_role, permission=permissions[perm_key])
            self.stdout.write(self.style.SUCCESS('  Created role: Guest'))
        
        # Create test users
        self.stdout.write('Creating test users...')
        
        # Admin user
        admin_user, created = User.objects.get_or_create(
            email='admin@example.com',
            defaults={'is_active': True, 'is_staff': True, 'is_superuser': True}
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            UserRole.objects.get_or_create(user=admin_user, role=admin_role)
            self.stdout.write(self.style.SUCCESS('  Created user: admin@example.com (password: admin123)'))
        
        # Manager user
        manager_user, created = User.objects.get_or_create(
            email='manager@example.com',
            defaults={'is_active': True}
        )
        if created:
            manager_user.set_password('manager123')
            manager_user.save()
            from apps.users.models import UserProfile
            UserProfile.objects.get_or_create(
                user=manager_user,
                defaults={
                    'first_name': 'Manager',
                    'last_name': 'User',
                    'middle_name': ''
                }
            )
            UserRole.objects.get_or_create(user=manager_user, role=manager_role)
            self.stdout.write(self.style.SUCCESS('  Created user: manager@example.com (password: manager123)'))
        
        # Regular user
        regular_user, created = User.objects.get_or_create(
            email='user@example.com',
            defaults={'is_active': True}
        )
        if created:
            regular_user.set_password('user123')
            regular_user.save()
            from apps.users.models import UserProfile
            UserProfile.objects.get_or_create(
                user=regular_user,
                defaults={
                    'first_name': 'Regular',
                    'last_name': 'User',
                    'middle_name': ''
                }
            )
            UserRole.objects.get_or_create(user=regular_user, role=user_role)
            self.stdout.write(self.style.SUCCESS('  Created user: user@example.com (password: user123)'))
        
        # Guest user
        guest_user, created = User.objects.get_or_create(
            email='guest@example.com',
            defaults={'is_active': True}
        )
        if created:
            guest_user.set_password('guest123')
            guest_user.save()
            from apps.users.models import UserProfile
            UserProfile.objects.get_or_create(
                user=guest_user,
                defaults={
                    'first_name': 'Guest',
                    'last_name': 'User',
                    'middle_name': ''
                }
            )
            UserRole.objects.get_or_create(user=guest_user, role=guest_role)
            self.stdout.write(self.style.SUCCESS('  Created user: guest@example.com (password: guest123)'))
        
        self.stdout.write(self.style.SUCCESS('\nTest data initialization completed!'))
        self.stdout.write('\nTest users:')
        self.stdout.write('  - admin@example.com / admin123 (Admin role)')
        self.stdout.write('  - manager@example.com / manager123 (Manager role)')
        self.stdout.write('  - user@example.com / user123 (User role)')
        self.stdout.write('  - guest@example.com / guest123 (Guest role)')

