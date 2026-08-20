# For beginners: This file (apps/payments/models.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

"""
Models for payment handling.
"""

import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from apps.users.models import User


# For beginners: This class 'Payment' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'Payment' groups related data and behavior
# so other parts of the app can use one structured object.
class Payment(models.Model):
    """Payment transaction model."""

    # For beginners: This class 'PaymentTypeChoices' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'PaymentTypeChoices' groups related data and behavior
    # so other parts of the app can use one structured object.
    class PaymentTypeChoices(models.TextChoices):
        PREMIUM = 'premium', 'Premium'
        CLAIM_PAYOUT = 'claim_payout', 'Claim Payout'

    # For beginners: This class 'PaymentDirectionChoices' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'PaymentDirectionChoices' groups related data and behavior
    # so other parts of the app can use one structured object.
    class PaymentDirectionChoices(models.TextChoices):
        INBOUND = 'inbound', 'Inbound (C2B)'
        OUTBOUND = 'outbound', 'Outbound (B2C)'

    # For beginners: This class 'StatusChoices' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'StatusChoices' groups related data and behavior
    # so other parts of the app can use one structured object.
    class StatusChoices(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        FAILED = 'failed', 'Failed'
        REFUNDED = 'refunded', 'Refunded'

    payment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    plan_id = models.ForeignKey(
        'plans.InsurancePlan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    chama_id = models.ForeignKey(
        'chamas.Chama',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    payment_type = models.CharField(max_length=20, choices=PaymentTypeChoices.choices)
    payment_direction = models.CharField(max_length=10, choices=PaymentDirectionChoices.choices)
    mpesa_ref = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
    )
    failure_reason = models.TextField(blank=True)
    initiated_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True, null=True)


    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    class Meta:
        db_table = 'payments_payment'
        ordering = ['-initiated_at']
        indexes = [
            models.Index(fields=['user_id', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['mpesa_ref']),
        ]

    # For beginners: This function '__str__' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function '__str__' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def __str__(self):
        return f"Payment {self.payment_id} - KES {self.amount}"
