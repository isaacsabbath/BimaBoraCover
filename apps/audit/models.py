# For beginners: This file (apps/audit/models.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

"""
=================================================
AUDIT LOG MODEL — Immutable Event Log
=================================================

This file defines the AuditLog model, which records every significant
action in the system. It is INSERT-ONLY: once a record is written, it
can never be modified or deleted. This is enforced in Python.

PURPOSE:
    - Compliance: Regulatory requirements often demand an unalterable
      record of who did what and when.
    - Debugging: When something goes wrong, the audit log shows the
      sequence of events leading up to it.
    - Security: Detecting unauthorized access attempts or suspicious
      patterns of behavior.

WHAT GETS LOGGED:
    - User registrations (via signal in apps.users.signals)
    - Claim submissions, approvals, rejections, info requests
    - Any other event the application explicitly writes to AuditLog

WHY A SEPARATE MODEL (not just Django's LogEntry):
    - Django's admin log only tracks admin actions. We need to track
      actions that happen via the API and template views too.
    - We need custom metadata (IP address, user agent, arbitrary JSON).
    - We need different querying patterns (by event_type, target model).

HOW IT WORKS:
    The save() and delete() methods are overridden to raise errors
    if any code tries to modify an existing record. New records are
    created normally via AuditLog.objects.create(...).
"""

import uuid
from django.db import models
from apps.users.models import User


# For beginners: This class 'AuditLog' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'AuditLog' groups related data and behavior
# so other parts of the app can use one structured object.
class AuditLog(models.Model):
    """
    An INSERT-only audit log recording system events.

    Why this is INSERT-only:
        - Audit logs must be tamper-proof for regulatory compliance.
        - If a record could be modified, an attacker could cover their tracks.
        - If a record could be deleted, evidence could be destroyed.

    Lifecycle:
        1. Created when a significant event happens (e.g., claim submitted).
        2. Never updated or deleted after creation.
        3. Read-only in the Django admin (no add/change/delete buttons).

    What each field records:
        - event_type: A machine-readable label like 'claim_submitted'.
        - actor_id: The User who performed the action (nullable for system
          events or anonymous actions).
        - target_model: The type of object affected (e.g., 'Claim', 'User').
        - target_id: The primary key of the affected object.
        - ip_address: Where the request came from (for security analysis).
        - user_agent: What browser or client was used.
        - metadata: Arbitrary JSON payload with event-specific details.

    Who writes to this:
        - apps.users.signals.log_user_event (on user registration)
        - apps.claims.views._write_audit_entry (on claim actions)
        - Any other code that calls AuditLog.objects.create(...)

    Who reads from this:
        - Django admin (read-only view).
        - Compliance/auditing tools.
        - Debugging during development.
    """

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

    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    class Meta:
        db_table = 'audit_auditlog'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type']),
            models.Index(fields=['target_model']),
            models.Index(fields=['actor_id']),
            models.Index(fields=['created_at']),
        ]

    # For beginners: This function 'save' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'save' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def save(self, *args, **kwargs):
        # Override save to prevent updates.
        if not self._state.adding:
            raise ValueError("AuditLog records cannot be modified after creation")
        super().save(*args, **kwargs)

    # For beginners: This function 'delete' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'delete' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def delete(self, *args, **kwargs):
        # Override delete to prevent deletions."""
        raise ValueError("AuditLog records cannot be deleted")

    # For beginners: This function '__str__' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function '__str__' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def __str__(self):
        return f"{self.event_type} - {self.target_model} ({self.created_at})"