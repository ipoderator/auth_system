from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Resource, Action, Permission, Role, UserRole
from .serializers import (
    ResourceSerializer,
    ActionSerializer,
    PermissionSerializer,
    RoleSerializer,
    UserRoleSerializer,
    AssignRoleToUserSerializer,
    AssignPermissionToRoleSerializer
)
from .permissions import IsAdmin


class ResourceViewSet(viewsets.ModelViewSet):
    """ViewSet для управления ресурсами (только для администраторов)."""

    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
    permission_classes = [IsAdmin]


class ActionViewSet(viewsets.ModelViewSet):
    """ViewSet для управления действиями (только для администраторов)."""

    queryset = Action.objects.all()
    serializer_class = ActionSerializer
    permission_classes = [IsAdmin]


class PermissionViewSet(viewsets.ModelViewSet):
    """ViewSet для управления разрешениями (только для администраторов)."""

    queryset = Permission.objects.select_related(
        'resource', 'action'
    ).all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAdmin]

    @action(detail=False, methods=['post'], url_path='create-by-names')
    def create_by_names(self, request):
        """Создать разрешение по именам ресурса и действия."""
        resource_name = request.data.get('resource_name')
        action_name = request.data.get('action_name')

        if not resource_name or not action_name:
            return Response(
                {'error': 'Требуются resource_name и action_name'},
                status=status.HTTP_400_BAD_REQUEST
            )

        permission, created = Permission.get_or_create_permission(
            resource_name,
            action_name
        )
        serializer = PermissionSerializer(permission)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


class RoleViewSet(viewsets.ModelViewSet):
    """ViewSet для управления ролями (только для администраторов)."""

    queryset = Role.objects.prefetch_related('permissions').all()
    serializer_class = RoleSerializer
    permission_classes = [IsAdmin]

    @action(detail=True, methods=['post'], url_path='permissions')
    def assign_permission(self, request, pk=None):
        """Назначить разрешение роли."""
        role = self.get_object()
        serializer = AssignPermissionToRoleSerializer(data={
            'role_id': role.id,
            **request.data
        })

        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'Разрешение успешно назначено'},
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=True,
        methods=['delete'],
        url_path='permissions/(?P<permission_id>[^/.]+)'
    )
    def remove_permission(self, request, pk=None, permission_id=None):
        """Удалить разрешение из роли."""
        from .models import RolePermission

        role = self.get_object()
        try:
            role_permission = RolePermission.objects.get(
                role=role,
                permission_id=permission_id
            )
            role_permission.delete()
            return Response(
                {'message': 'Разрешение успешно удалено'},
                status=status.HTTP_200_OK
            )
        except RolePermission.DoesNotExist:
            return Response(
                {'error': 'Разрешение не найдено для этой роли'},
                status=status.HTTP_404_NOT_FOUND
            )


class UserRoleViewSet(viewsets.ModelViewSet):
    """ViewSet для управления назначениями ролей пользователям."""

    queryset = UserRole.objects.select_related('user', 'role').all()
    serializer_class = UserRoleSerializer
    permission_classes = [IsAdmin]

    @action(detail=False, methods=['post'], url_path='assign')
    def assign_role(self, request):
        """Назначить роль пользователю."""
        serializer = AssignRoleToUserSerializer(data=request.data)

        if serializer.is_valid():
            user_role = serializer.save()
            response_serializer = UserRoleSerializer(user_role)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=False,
        methods=['get'],
        url_path='user/(?P<user_id>[^/.]+)'
    )
    def get_user_roles(self, request, user_id=None):
        """Получить все роли для конкретного пользователя."""
        user_roles = UserRole.objects.filter(
            user_id=user_id
        ).select_related('role')
        serializer = UserRoleSerializer(user_roles, many=True)
        return Response(serializer.data)
