# For beginners: This file (apps/users/signals.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

"""
Signal handlers for audit logging.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.audit.models import AuditLog


@receiver(post_save, sender='users.User')
# For beginners: This function 'log_user_event' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
# For beginners: This function 'log_user_event' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
def log_user_event(sender, instance, created, **kwargs):
    """Log user creation events only."""
    if not created:
        return  # Skip updates to avoid triggering on last_login, session saves, etc.

    try:
        AuditLog.objects.create(
            event_type='user_registered',
            actor_id=instance,
            target_model='User',
            target_id=instance.id,
            metadata={
                'role': instance.role,
                'kyc_status': instance.kyc_status
            }
        )
    except Exception:
        pass  # Never block user creation due to audit failure
