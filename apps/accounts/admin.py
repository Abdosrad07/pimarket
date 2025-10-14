from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PhoneOTP, UserLocation


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['phone_number', 'display_name', 'is_phone_verified', 'date_joined']
    list_filter = ['is_phone_verified', 'is_staff', 'is_active']
    search_fields = ['phone_number', 'display_name']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('Personal info', {'fields': ('display_name', 'avatar')}),
        ('Verification', {'fields': ('is_phone_verified',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'display_name', 'password1', 'password2'),
        }),
    )


@admin.register(PhoneOTP)
class PhoneOTPAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'otp', 'created_at', 'expires_at', 'attempts', 'is_verified']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['phone_number']
    readonly_fields = ['created_at']


@admin.register(UserLocation)
class UserLocationAdmin(admin.ModelAdmin):
    list_display = ['user', 'latitude', 'longitude', 'city', 'is_current', 'updated_at']
    list_filter = ['is_current', 'country']
    search_fields = ['user__phone_number', 'user__display_name', 'city']
    readonly_fields = ['updated_at']