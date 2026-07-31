"""
Models for audit logging.
"""

import uuid
from django.db import models
from apps.users.models import User


class AuditLog(models.Model):
    """INSERT-only audit log for all system events."""
    
    log_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=60)
    actor_id = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='audit_logs_created'
    )
    target_model = models.CharField(max_length=50)
    target_id = models.UUIDField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_auditlog'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type']),
            models.Index(fields=['target_model']),
            models.Index(fields=['actor_id']),
            models.Index(fields=['created_at']),
        ]
    
    def save(self, *args, **kwargs):
    # Override save to prevent updates.
        if not self._state.adding:
            raise ValueError("AuditLog records cannot be modified after creation")
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Override delete to prevent deletions."""
        raise ValueError("AuditLog records cannot be deleted")
    
    def __str__(self):
        return f"{self.event_type} - {self.target_model} ({self.created_at})"
