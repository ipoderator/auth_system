from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для UserProfile."""

    class Meta:
        model = UserProfile
        fields = (
            'first_name', 'last_name', 'middle_name',
            'created_at', 'updated_at'
        )
        read_only_fields = ('created_at', 'updated_at')


class UserRegistrationSerializer(serializers.Serializer):
    """Сериализатор для регистрации пользователя."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True
    )
    first_name = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True
    )
    last_name = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True
    )
    middle_name = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True
    )

    def validate(self, attrs):
        """Проверка совпадения паролей."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password_confirm": "Пароли не совпадают."
            })
        return attrs

    def validate_email(self, value):
        """Проверка уникальности email."""
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Пользователь с таким email уже существует."
            )
        return value

    def create(self, validated_data):
        """Создание нового пользователя и профиля."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        first_name = validated_data.pop('first_name', '')
        last_name = validated_data.pop('last_name', '')
        middle_name = validated_data.pop('middle_name', '')

        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=password
        )

        UserProfile.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name
        )

        return user


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели User."""

    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = CustomUser
        fields = (
            'id', 'email', 'is_active', 'date_joined',
            'last_login', 'profile'
        )
        read_only_fields = (
            'id', 'email', 'is_active', 'date_joined', 'last_login'
        )


class UserUpdateSerializer(serializers.Serializer):
    """Сериализатор для обновления профиля пользователя."""

    first_name = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True
    )
    last_name = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True
    )
    middle_name = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True
    )

    def update(self, instance, validated_data):
        """Обновление профиля пользователя."""
        profile, created = UserProfile.objects.get_or_create(user=instance)

        if 'first_name' in validated_data:
            profile.first_name = validated_data['first_name']
        if 'last_name' in validated_data:
            profile.last_name = validated_data['last_name']
        if 'middle_name' in validated_data:
            profile.middle_name = validated_data['middle_name']

        profile.save()
        return instance


class LoginSerializer(serializers.Serializer):
    """Сериализатор для входа."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
