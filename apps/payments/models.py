"""
Models for payment handling.
"""

import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from apps.users.models import User


class Payment(models.Model):
    """Payment transaction model."""

    class PaymentTypeChoices(models.TextChoices):
        PREMIUM = 'premium', 'Premium'
        CLAIM_PAYOUT = 'claim_payout', 'Claim Payout'

    class PaymentDirectionChoices(models.TextChoices):
        INBOUND = 'inbound', 'Inbound (C2B)'
        OUTBOUND = 'outbound', 'Outbound (B2C)'

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
    mpesa_ref = models.CharField(max_length=30, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
    )
    failure_reason = models.TextField(blank=True)
    initiated_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True, null=True)


    class Meta:
        db_table = 'payments_payment'
        ordering = ['-initiated_at']
        indexes = [
            models.Index(fields=['user_id', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['mpesa_ref']),
        ]

    def __str__(self):
        return f"Payment {self.payment_id} - KES {self.amount}"
