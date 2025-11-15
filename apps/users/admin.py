from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, UserProfile, Token


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    """Админ-интерфейс для CustomUser."""
    list_display = (
        'email', 'is_active', 'is_staff', 'is_superuser',
        'date_joined', 'last_login'
    )
    list_filter = (
        'is_active', 'is_staff', 'is_superuser', 'date_joined'
    )
    search_fields = ('email',)
    ordering = ('-date_joined',)
    # Убираем groups и user_permissions, которых нет в CustomUser
    filter_horizontal = ()

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Админ-интерфейс для UserProfile."""
    list_display = (
        'user', 'first_name', 'last_name', 'middle_name', 'created_at'
    )
    search_fields = ('user__email', 'first_name', 'last_name')
    list_filter = ('created_at',)


@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    """Админ-интерфейс для Token."""
    list_display = ('user', 'token', 'created_at', 'expires_at', 'is_active')
    list_filter = ('is_active', 'created_at', 'expires_at')
    search_fields = ('user__email', 'token')
    readonly_fields = ('token', 'created_at')
    ordering = ('-created_at',)
