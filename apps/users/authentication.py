from rest_framework import authentication, exceptions
from loguru import logger
from .models import Token


class CustomTokenAuthentication(authentication.BaseAuthentication):
    """Пользовательская аутентификация на основе токенов."""

    def authenticate(self, request):
        """Аутентификация запроса с использованием токена."""
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header:
            logger.debug("Запрос без заголовка авторизации")
            return None

        try:
            auth_type, token_string = auth_header.split(' ', 1)
        except ValueError:
            logger.warning("Неверный формат заголовка авторизации")
            return None

        if auth_type.lower() != 'token':
            logger.debug(f"Неподдерживаемый тип авторизации: {auth_type}")
            return None

        try:
            token = Token.objects.select_related('user').get(
                token=token_string,
                is_active=True
            )
            logger.debug(f"Токен найден для пользователя: {token.user.email}")
        except Token.DoesNotExist:
            logger.warning(f"Попытка аутентификации с неверным токеном")
            raise exceptions.AuthenticationFailed('Неверный токен')

        # Проверка истечения токена
        if token.is_expired():
            logger.info(f"Токен истек для пользователя: {token.user.email}")
            token.invalidate()
            raise exceptions.AuthenticationFailed('Токен истек')

        # Проверка активности пользователя
        if not token.user.is_active:
            logger.warning(
                f"Попытка входа неактивного пользователя: {token.user.email}"
            )
            raise exceptions.AuthenticationFailed(
                'Учетная запись пользователя отключена'
            )

        logger.debug(f"Успешная аутентификация пользователя: {token.user.email}")
        return (token.user, token)
