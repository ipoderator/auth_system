from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings
from loguru import logger
from .models import CustomUser, Token
from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    UserUpdateSerializer,
    LoginSerializer
)


class IsAuthenticatedWithLogging(permissions.IsAuthenticated):
    """IsAuthenticated с логированием для диагностики."""

    def has_permission(self, request, view):
        result = super().has_permission(request, view)
        if not result:
            logger.warning(
                f"Доступ запрещен для {request.user} "
                f"(аутентифицирован: {request.user.is_authenticated}, "
                f"активен: {getattr(request.user, 'is_active', 'N/A')})"
            )
        else:
            logger.debug(
                f"Доступ разрешен для {request.user.email} "
                f"к {view.__class__.__name__}.{view.action}"
            )
        return result


class AuthViewSet(viewsets.ViewSet):
    """ViewSet для операций аутентификации."""

    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['post'], url_path='register')
    def register(self, request):
        """Регистрация нового пользователя."""
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            logger.info(f"Новый пользователь зарегистрирован: {user.email}")
            user_serializer = UserSerializer(user)
            return Response(
                {
                    'message': 'Пользователь успешно зарегистрирован',
                    'user': user_serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        logger.warning(f"Ошибка регистрации: {serializer.errors}")
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        """Вход пользователя и возврат токена."""
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Ошибка валидации при входе: {serializer.errors}")
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            logger.warning(f"Попытка входа с несуществующим email: {email}")
            return Response(
                {'error': 'Неверный email или пароль'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            logger.warning(f"Попытка входа неактивного пользователя: {email}")
            return Response(
                {'error': 'Учетная запись пользователя отключена'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.check_password(password):
            logger.warning(f"Неверный пароль для пользователя: {email}")
            return Response(
                {'error': 'Неверный email или пароль'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Создать или получить существующий активный токен
        expiration_hours = getattr(settings, 'TOKEN_EXPIRATION_HOURS', 24)
        token = Token.create_token(user, expiration_hours)
        logger.info(f"Успешный вход пользователя: {email}")

        user_serializer = UserSerializer(user)
        return Response({
            'token': token.token,
            'user': user_serializer.data,
            'expires_at': token.expires_at
        }, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['post'],
        url_path='logout',
        permission_classes=[permissions.IsAuthenticated]
    )
    def logout(self, request):
        """Выход пользователя путем инвалидации токена."""
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if auth_header:
            try:
                auth_type, token_string = auth_header.split(' ', 1)
                if auth_type.lower() == 'token':
                    try:
                        token = Token.objects.get(
                            token=token_string,
                            user=request.user
                        )
                        token.invalidate()
                        logger.info(f"Пользователь вышел: {request.user.email}")
                    except Token.DoesNotExist:
                        logger.warning(
                            f"Токен не найден при выходе для пользователя: "
                            f"{request.user.email}"
                        )
            except ValueError:
                logger.warning("Неверный формат заголовка авторизации при выходе")

        return Response(
            {'message': 'Выход выполнен успешно'},
            status=status.HTTP_200_OK
        )


class ProfileViewSet(viewsets.ViewSet):
    """ViewSet для операций с профилем пользователя."""

    permission_classes = [IsAuthenticatedWithLogging]

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Получить профиль текущего пользователя."""
        logger.debug(
            f"Запрос профиля от пользователя: {request.user.email}, "
            f"аутентифицирован: {request.user.is_authenticated}, "
            f"активен: {request.user.is_active}"
        )
        serializer = UserSerializer(request.user)
        logger.info(f"Профиль успешно получен для пользователя: {request.user.email}")
        return Response(serializer.data)

    @action(detail=False, methods=['put'])
    def update_profile(self, request):
        """Обновить профиль текущего пользователя."""
        serializer = UserUpdateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.update(request.user, serializer.validated_data)
            user_serializer = UserSerializer(request.user)
            return Response(user_serializer.data)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['patch'])
    def partial_update_profile(self, request):
        """Частично обновить профиль текущего пользователя."""
        serializer = UserUpdateSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            serializer.update(request.user, serializer.validated_data)
            user_serializer = UserSerializer(request.user)
            return Response(user_serializer.data)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['delete'])
    def delete_account(self, request):
        """Мягкое удаление учетной записи пользователя."""
        user_email = request.user.email
        # Инвалидировать все токены
        tokens_count = Token.objects.filter(
            user=request.user,
            is_active=True
        ).update(is_active=False)

        # Мягкое удаление пользователя
        request.user.is_active = False
        request.user.save()

        logger.info(
            f"Аккаунт удален (мягкое удаление): {user_email}, "
            f"инвалидировано токенов: {tokens_count}"
        )

        return Response(
            {'message': 'Аккаунт успешно удален'},
            status=status.HTTP_200_OK
        )
