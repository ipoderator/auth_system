from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
import secrets


class CustomUserManager(BaseUserManager):
    """Custom user manager for CustomUser model."""

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser):
    """Custom user model using email as username."""

    email = models.EmailField(unique=True, verbose_name='Email')
    is_active = models.BooleanField(default=True, verbose_name='Active')
    is_staff = models.BooleanField(
        default=False,
        verbose_name='Staff status'
    )
    is_superuser = models.BooleanField(
        default=False,
        verbose_name='Superuser status'
    )
    date_joined = models.DateTimeField(
        default=timezone.now,
        verbose_name='Date joined'
    )
    last_login = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Last login'
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        db_table = 'users'

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        """Check if user has a specific permission."""
        return self.is_superuser

    def has_module_perms(self, app_label):
        """Check if user has permissions to view the app."""
        return self.is_superuser


class UserProfile(models.Model):
    """User profile with additional information."""

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='User'
    )
    first_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='First name'
    )
    last_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Last name'
    )
    middle_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Middle name'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created at'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated at'
    )

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        db_table = 'user_profiles'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.user.email})"


class Token(models.Model):
    """Custom token model for authentication."""

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='tokens',
        verbose_name='User'
    )
    token = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name='Token'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created at'
    )
    expires_at = models.DateTimeField(verbose_name='Expires at')
    is_active = models.BooleanField(default=True, verbose_name='Active')

    class Meta:
        verbose_name = 'Token'
        verbose_name_plural = 'Tokens'
        db_table = 'tokens'
        indexes = [
            models.Index(fields=['token', 'is_active']),
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        return f"Token for {self.user.email}"

    @classmethod
    def generate_token(cls):
        """Generate a secure random token."""
        return secrets.token_urlsafe(48)

    @classmethod
    def create_token(cls, user, expiration_hours=24):
        """Create a new token for a user."""
        from django.utils import timezone
        from datetime import timedelta

        token_string = cls.generate_token()
        expires_at = timezone.now() + timedelta(hours=expiration_hours)

        token = cls.objects.create(
            user=user,
            token=token_string,
            expires_at=expires_at
        )
        return token

    def is_expired(self):
        """Проверка истечения токена."""
        from django.utils import timezone
        return timezone.now() > self.expires_at

    def invalidate(self):
        """Инвалидация токена."""
        self.is_active = False
        self.save()
