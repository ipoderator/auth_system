from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ResourceViewSet,
    ActionViewSet,
    PermissionViewSet,
    RoleViewSet,
    UserRoleViewSet
)

router = DefaultRouter()
router.register(r'resources', ResourceViewSet, basename='resource')
router.register(r'actions', ActionViewSet, basename='action')
router.register(r'permissions', PermissionViewSet, basename='permission')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'user-roles', UserRoleViewSet, basename='user-role')

urlpatterns = [
    path('', include(router.urls)),
]

