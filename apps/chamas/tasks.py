# For beginners: This file (apps/chamas/tasks.py) contains background jobs
# run by django-q2's worker process (`python manage.py qcluster`), not by
# the web request/response cycle — so inviting a member doesn't block on
# SMTP while the email actually sends.

"""
=================================================
CHAMA TASKS — async invite emails
=================================================

HOW TO QUEUE:
    from apps.chamas.tasks import queue_chama_invite_email
    queue_chama_invite_email(email, chama_name, invite_link)

REQUIREMENTS (same as blockchain anchoring — already enabled):
    - 'django_q' in INSTALLED_APPS
    - migrations run: `python manage.py migrate django_q`
    - a worker running: `python manage.py qcluster`
    - EMAIL_HOST / EMAIL_HOST_USER / EMAIL_HOST_PASSWORD set in .env
      (defaults to Django's console backend, which just prints the email
      to the qcluster terminal instead of sending it — handy for local dev,
      but you won't get a real email until real SMTP creds are set)
"""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django_q.tasks import async_task

logger = logging.getLogger(__name__)


def queue_chama_invite_email(email, chama_name, invite_link, inviter_name=''):
    # For beginners: This function 'queue_chama_invite_email' performs one
    # reusable task. Other parts of the app call it to avoid duplicating logic.
    """Schedule a chama invite email. Fire-and-forget."""
    async_task(
        'apps.chamas.tasks.send_chama_invite_email',
        email, chama_name, invite_link, inviter_name,
    )


def send_chama_invite_email(email, chama_name, invite_link, inviter_name=''):
    """Worker entrypoint: actually send the invite email."""
    inviter_line = f'{inviter_name} has invited you' if inviter_name else "You've been invited"

    subject = f'{inviter_line} to join {chama_name} on Bima Afya'
    message = (
        f'{inviter_line} to join "{chama_name}" on Bima Afya.\n\n'
        f'Click the link below to accept and join the group:\n'
        f'{invite_link}\n\n'
        f'This invitation link expires in 48 hours.\n\n'
        f"If you weren't expecting this invite, you can safely ignore this email."
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info('Chama invite email sent to %s for "%s"', email, chama_name)
    except Exception:
        logger.exception('Failed to send chama invite email to %s', email)
