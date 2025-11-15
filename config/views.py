from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import render


@require_http_methods(["GET"])
def api_root(request):
    """Главная страница API с информацией о доступных endpoints."""
    base_url = request.build_absolute_uri('/').rstrip('/')

    return JsonResponse({
        'message': 'Auth System API',
        'version': '1.0',
        'base_url': base_url,
        'frontend': {
            'home': f'{base_url}/',
            'login': f'{base_url}/auth/login/',
            'register': f'{base_url}/auth/register/',
            'profile': f'{base_url}/auth/profile/',
        },
        'endpoints': {
            'authentication': {
                'register': {
                    'method': 'POST',
                    'url': f'{base_url}/api/auth/register/',
                    'description': 'Регистрация нового пользователя',
                },
                'login': {
                    'method': 'POST',
                    'url': f'{base_url}/api/auth/login/',
                    'description': 'Вход в систему, получение токена',
                },
                'logout': {
                    'method': 'POST',
                    'url': f'{base_url}/api/auth/logout/',
                    'description': 'Выход из системы, инвалидация токена',
                    'auth_required': True,
                },
                'profile': {
                    'get': {
                        'method': 'GET',
                        'url': f'{base_url}/api/auth/profile/me/',
                        'description': (
                            'Получение профиля текущего пользователя'
                        ),
                        'auth_required': True,
                    },
                    'update': {
                        'method': 'PUT',
                        'url': f'{base_url}/api/auth/profile/update_profile/',
                        'description': 'Обновление профиля',
                        'auth_required': True,
                    },
                    'partial_update': {
                        'method': 'PATCH',
                        'url': (
                            f'{base_url}/api/auth/profile/'
                            f'partial_update_profile/'
                        ),
                        'description': 'Частичное обновление профиля',
                        'auth_required': True,
                    },
                    'delete': {
                        'method': 'DELETE',
                        'url': (
                            f'{base_url}/api/auth/profile/delete_account/'
                        ),
                        'description': 'Мягкое удаление аккаунта',
                        'auth_required': True,
                    },
                }
            },
            'admin': {
                'resources': f'{base_url}/api/admin/resources/',
                'actions': f'{base_url}/api/admin/actions/',
                'permissions': f'{base_url}/api/admin/permissions/',
                'roles': f'{base_url}/api/admin/roles/',
                'user_roles': f'{base_url}/api/admin/user-roles/',
                'note': 'Требуется роль Admin',
            },
            'business_objects': {
                'products': {
                    'url': f'{base_url}/api/products/',
                    'required_permissions': [
                        'products.list',
                        'products.read',
                        'products.create',
                        'products.update',
                        'products.delete',
                    ],
                },
                'orders': {
                    'url': f'{base_url}/api/orders/',
                    'required_permissions': [
                        'orders.list',
                        'orders.read',
                        'orders.create',
                        'orders.update',
                        'orders.delete',
                    ],
                },
                'reports': {
                    'url': f'{base_url}/api/reports/',
                    'required_permissions': [
                        'reports.list',
                        'reports.read',
                    ],
                },
            },
            'admin_panel': f'{base_url}/admin/',
        },
        'authentication': {
            'type': 'Token',
            'header_format': 'Authorization: Token <your-token>',
            'how_to_get_token': (
                'Отправьте POST запрос на /api/auth/login/ '
                'с email и password'
            ),
        },
        'test_users': {
            'admin': {
                'email': 'admin@example.com',
                'password': 'admin123',
                'role': 'Admin',
            },
            'manager': {
                'email': 'manager@example.com',
                'password': 'manager123',
                'role': 'Manager',
            },
            'user': {
                'email': 'user@example.com',
                'password': 'user123',
                'role': 'User',
            },
            'guest': {
                'email': 'guest@example.com',
                'password': 'guest123',
                'role': 'Guest',
            },
        },
        'error_codes': {
            '401': 'Unauthorized - требуется аутентификация',
            '403': 'Forbidden - недостаточно прав доступа',
            '404': 'Not Found - ресурс не найден',
            '400': 'Bad Request - неверные данные запроса',
        },
        'documentation': {
            'readme': 'См. README.md для подробной документации API',
            'frontend_guide': 'См. FRONTEND.md для использования фронтенда',
        },
    })


def login_view(request):
    """Страница входа."""
    return render(request, 'auth/login.html')


def register_view(request):
    """Страница регистрации."""
    return render(request, 'auth/register.html')


def profile_view(request):
    """Страница профиля."""
    return render(request, 'auth/profile.html')


def index_view(request):
    """Главная страница с редиректом."""
    return render(request, 'auth/index.html')
