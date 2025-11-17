from rest_framework import serializers
from .models import (
    Resource, Action, Permission, Role, RolePermission, UserRole
)
from apps.users.models import CustomUser


class ResourceSerializer(serializers.ModelSerializer):
    """Сериализатор для Resource."""

    class Meta:
        model = Resource
        fields = ('id', 'name', 'description', 'created_at')
        read_only_fields = ('id', 'created_at')


class ActionSerializer(serializers.ModelSerializer):
    """Сериализатор для Action."""

    class Meta:
        model = Action
        fields = ('id', 'name', 'description', 'created_at')
        read_only_fields = ('id', 'created_at')


class PermissionSerializer(serializers.ModelSerializer):
    """Сериализатор для Permission."""

    resource = ResourceSerializer(read_only=True)
    action = ActionSerializer(read_only=True)
    resource_id = serializers.IntegerField(write_only=True, required=False)
    action_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Permission
        fields = (
            'id', 'resource', 'action', 'resource_id',
            'action_id', 'created_at'
        )
        read_only_fields = ('id', 'created_at')

    def create(self, validated_data):
        resource_id = validated_data.pop('resource_id', None)
        action_id = validated_data.pop('action_id', None)

        if resource_id:
            validated_data['resource_id'] = resource_id
        if action_id:
            validated_data['action_id'] = action_id

        return super().create(validated_data)


class RoleSerializer(serializers.ModelSerializer):
    """Сериализатор для Role."""

    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Role
        fields = (
            'id', 'name', 'description', 'permissions',
            'permission_ids', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def create(self, validated_data):
        permission_ids = validated_data.pop('permission_ids', [])
        role = Role.objects.create(**validated_data)

        if permission_ids:
            permissions = Permission.objects.filter(id__in=permission_ids)
            for permission in permissions:
                RolePermission.objects.create(
                    role=role,
                    permission=permission
                )

        return role

    def update(self, instance, validated_data):
        permission_ids = validated_data.pop('permission_ids', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if permission_ids is not None:
            # Clear existing permissions
            RolePermission.objects.filter(role=instance).delete()
            # Add new permissions
            permissions = Permission.objects.filter(id__in=permission_ids)
            for permission in permissions:
                RolePermission.objects.create(
                    role=instance,
                    permission=permission
                )

        return instance


class UserRoleSerializer(serializers.ModelSerializer):
    """Сериализатор для UserRole."""

    user = serializers.StringRelatedField(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    role = RoleSerializer(read_only=True)
    role_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = UserRole
        fields = ('id', 'user', 'user_id', 'role', 'role_id', 'created_at')
        read_only_fields = ('id', 'created_at')

    def validate_user_id(self, value):
        """Проверка существования пользователя."""
        if not CustomUser.objects.filter(id=value).exists():
            raise serializers.ValidationError("Пользователь не существует.")
        return value

    def validate_role_id(self, value):
        """Проверка существования роли."""
        if not Role.objects.filter(id=value).exists():
            raise serializers.ValidationError("Роль не существует.")
        return value


class AssignRoleToUserSerializer(serializers.Serializer):
    """Сериализатор для назначения роли пользователю."""

    user_id = serializers.IntegerField(required=True)
    role_id = serializers.IntegerField(required=True)

    def validate_user_id(self, value):
        """Проверка существования пользователя."""
        if not CustomUser.objects.filter(id=value).exists():
            raise serializers.ValidationError("Пользователь не существует.")
        return value

    def validate_role_id(self, value):
        """Проверка существования роли."""
        if not Role.objects.filter(id=value).exists():
            raise serializers.ValidationError("Роль не существует.")
        return value

    def create(self, validated_data):
        """Создание назначения UserRole."""
        user_role, created = UserRole.objects.get_or_create(
            user_id=validated_data['user_id'],
            role_id=validated_data['role_id']
        )
        if not created:
            raise serializers.ValidationError(
                "Пользователь уже имеет эту роль."
            )
        return user_role


class AssignPermissionToRoleSerializer(serializers.Serializer):
    """Сериализатор для назначения разрешения роли."""

    role_id = serializers.IntegerField(required=True)
    permission_id = serializers.IntegerField(required=False)
    resource_name = serializers.CharField(required=False)
    action_name = serializers.CharField(required=False)

    def validate(self, attrs):
        """Проверка наличия permission_id или resource_name+action_name."""
        has_permission_id = attrs.get('permission_id')
        has_resource_and_action = (
            attrs.get('resource_name') and attrs.get('action_name')
        )
        if not has_permission_id and not has_resource_and_action:
            raise serializers.ValidationError(
                "Необходимо указать либо permission_id, "
                "либо resource_name и action_name."
            )
        return attrs

    def create(self, validated_data):
        """Создание назначения RolePermission."""
        from .models import Permission

        role_id = validated_data['role_id']

        if validated_data.get('permission_id'):
            permission_id = validated_data['permission_id']
        else:
            permission, _ = Permission.get_or_create_permission(
                validated_data['resource_name'],
                validated_data['action_name']
            )
            permission_id = permission.id

        role_permission, created = RolePermission.objects.get_or_create(
            role_id=role_id,
            permission_id=permission_id
        )
        if not created:
            raise serializers.ValidationError(
                "Роль уже имеет это разрешение."
            )
        return role_permission
