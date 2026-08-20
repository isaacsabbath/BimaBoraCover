# For beginners: This file (apps/audit/admin.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

"""
Django admin configuration for audit app.
"""

from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
# For beginners: This class 'AuditLogAdmin' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'AuditLogAdmin' groups related data and behavior
# so other parts of the app can use one structured object.
class AuditLogAdmin(admin.ModelAdmin):
    """Admin for AuditLog model (read-only)."""
    
    list_display = ('event_type', 'actor_id', 'target_model', 'created_at')
    list_filter = ('event_type', 'target_model', 'created_at')
    search_fields = ('event_type', 'actor_id__full_name')
    ordering = ('-created_at',)
    readonly_fields = ('log_id', 'event_type', 'actor_id', 'target_model', 'target_id', 'ip_address', 'user_agent', 'metadata', 'created_at')
    
    # For beginners: This function 'has_change_permission' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'has_change_permission' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def has_change_permission(self, request, obj=None):
        """Prevent editing audit logs."""
        return False
    
    # For beginners: This function 'has_delete_permission' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'has_delete_permission' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def has_delete_permission(self, request, obj=None):
        """Prevent deleting audit logs."""
        return False
    
    # For beginners: This function 'has_add_permission' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'has_add_permission' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def has_add_permission(self, request):
        """Prevent adding audit logs manually."""
        return False
