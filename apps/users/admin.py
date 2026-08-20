# For beginners: This file (apps/users/admin.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
# For beginners: This class 'UserAdmin' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'UserAdmin' groups related data and behavior
# so other parts of the app can use one structured object.
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        ('Authentication', {'fields': ('email', 'password')}),
        ('Profile', {'fields': ('full_name', 'national_id', 'phone_number')}),
        ('System', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('KYC', {
            'fields': ('kyc_status', 'kyc_verification_result', 'kyc_verified_at'),
            'classes': ('collapse',)
        }),
        ('OTP', {
            'fields': ('otp_code', 'otp_created_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'full_name', 'national_id', 'phone_number', 'role', 'is_active'),
        }),
    )

    list_display = ('email', 'full_name', 'phone_number', 'role', 'kyc_status', 'is_active', 'created_at')
    list_filter = ('role', 'kyc_status', 'is_active')
    search_fields = ('email', 'full_name', 'phone_number', 'national_id')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'id')
    actions = ['activate_users', 'deactivate_users', 'verify_kyc']

    # For beginners: This function 'verify_kyc' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'verify_kyc' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def verify_kyc(self, request, queryset):
        from django.utils import timezone
        queryset.update(kyc_status='verified', kyc_verified_at=timezone.now())
        self.message_user(request, f"{queryset.count()} user(s) KYC verified.")
    verify_kyc.short_description = "Mark KYC as verified"

    # For beginners: This function 'activate_users' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'activate_users' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} user(s) activated.")
    activate_users.short_description = "Activate selected users"

    # For beginners: This function 'deactivate_users' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'deactivate_users' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} user(s) deactivated.")
    deactivate_users.short_description = "Deactivate selected users"
