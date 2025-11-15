from rest_framework import authentication, exceptions
from django.utils import timezone
from .models import Token


class CustomTokenAuthentication(authentication.BaseAuthentication):
    """Пользовательская аутентификация на основе токенов."""
    
    def authenticate(self, request):
        """Аутентификация запроса с использованием токена."""
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header:
            return None
        
        try:
            auth_type, token_string = auth_header.split(' ', 1)
        except ValueError:
            return None
        
        if auth_type.lower() != 'token':
            return None
        
        try:
            token = Token.objects.select_related('user').get(
                token=token_string,
                is_active=True
            )
        except Token.DoesNotExist:
            raise exceptions.AuthenticationFailed('Неверный токен')
        
        # Проверка истечения токена
        if token.is_expired():
            token.invalidate()
            raise exceptions.AuthenticationFailed('Токен истек')
        
        # Проверка активности пользователя
        if not token.user.is_active:
            raise exceptions.AuthenticationFailed('Учетная запись пользователя отключена')
        
        return (token.user, token)

