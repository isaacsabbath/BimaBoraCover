"""
Django admin configuration for audit app.
"""

from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin for AuditLog model (read-only)."""
    
    list_display = ('event_type', 'actor_id', 'target_model', 'created_at')
    list_filter = ('event_type', 'target_model', 'created_at')
    search_fields = ('event_type', 'actor_id__full_name')
    ordering = ('-created_at',)
    readonly_fields = ('log_id', 'event_type', 'actor_id', 'target_model', 'target_id', 'ip_address', 'user_agent', 'metadata', 'created_at')
    
    def has_change_permission(self, request, obj=None):
        """Prevent editing audit logs."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deleting audit logs."""
        return False
    
    def has_add_permission(self, request):
        """Prevent adding audit logs manually."""
        return False
