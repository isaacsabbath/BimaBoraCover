"""
Signal handlers for audit logging.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.audit.models import AuditLog


@receiver(post_save, sender='users.User')
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
