"""
URL configuration for auth_system project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    api_root, login_view, register_view, profile_view, index_view
)

urlpatterns = [
    path('api/', api_root, name='api-root'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),
    path('api/admin/', include('apps.authorization.urls')),
    path('api/', include('apps.mock_business.urls')),
    # Frontend routes
    path('', index_view, name='index'),
    path('auth/login/', login_view, name='login'),
    path('auth/register/', register_view, name='register'),
    path('auth/profile/', profile_view, name='profile'),
]

# Serve static files during development
if settings.DEBUG:
    static_root = (
        settings.STATICFILES_DIRS[0]
        if settings.STATICFILES_DIRS
        else None
    )
    urlpatterns += static(settings.STATIC_URL, document_root=static_root)
