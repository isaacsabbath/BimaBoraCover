# For beginners: This file (apps/chamas/tasks.py) contains background jobs
# run by django-q2's worker process (`python manage.py qcluster`), not by
# the web request/response cycle — so inviting a member doesn't block on
# SMTP while the email actually sends.

"""
=================================================
CHAMA TASKS — async invite emails + SMS
=================================================

HOW TO QUEUE:
    from apps.chamas.tasks import queue_chama_invite_email, queue_chama_invite_sms
    queue_chama_invite_email(email, chama_name, invite_link)
    queue_chama_invite_sms(phone_number, chama_name, invite_link)

REQUIREMENTS (same as blockchain anchoring — already enabled):
    - 'django_q' in INSTALLED_APPS
    - migrations run: `python manage.py migrate django_q`
    - a worker running: `python manage.py qcluster`
    - EMAIL_HOST / EMAIL_HOST_USER / EMAIL_HOST_PASSWORD set in .env
      (defaults to Django's console backend, which just prints the email
      to the qcluster terminal instead of sending it — handy for local dev,
      but you won't get a real email until real SMTP creds are set)
    - AT_USERNAME / AT_API_KEY set in .env for SMS (reuses the same
      Africa's Talking account as apps.users.services.otp; defaults to
      'sandbox' username, which only delivers to numbers registered as
      test numbers in your AT sandbox app)
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


def queue_chama_invite_sms(phone_number, chama_name, invite_link, inviter_name=''):
    # For beginners: This function 'queue_chama_invite_sms' performs one
    # reusable task. Other parts of the app call it to avoid duplicating logic.
    """Schedule a chama invite SMS. Fire-and-forget."""
    async_task(
        'apps.chamas.tasks.send_chama_invite_sms',
        phone_number, chama_name, invite_link, inviter_name,
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


def send_chama_invite_sms(phone_number, chama_name, invite_link, inviter_name=''):
    """Worker entrypoint: send the invite via Africa's Talking SMS.
    Reuses the same AT account/credentials as apps.users.services.otp."""
    import africastalking

    inviter_line = f'{inviter_name} invited you' if inviter_name else "You've been invited"
    message = f'{inviter_line} to join "{chama_name}" on Bima Afya. Join here: {invite_link}'

    try:
        username = settings.AT_USERNAME
        api_key = settings.AT_API_KEY

        if not api_key:
            raise ValueError("Africa's Talking credentials not configured")

        africastalking.initialize(username, api_key)
        sms = africastalking.SMS

        response = sms.send(
            message=message,
            recipients=[phone_number],
            sender_id=settings.AT_SENDER_ID,
        )

        if response['SMSMessageData']['Recipients'][0]['statusCode'] != 0:
            raise Exception(f'SMS send failed: {response}')

        logger.info('Chama invite SMS sent to %s for "%s"', phone_number, chama_name)
    except Exception:
        logger.exception('Failed to send chama invite SMS to %s', phone_number)
