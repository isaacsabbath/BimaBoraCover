"""
Models for claims management.
"""

import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MinLengthValidator
from apps.users.models import User


class Claim(models.Model):
    """Insurance claim model."""
    
    class ClaimTypeChoices(models.TextChoices):
        MEDICAL = 'medical', 'Medical'
        ACCIDENT = 'accident', 'Accident'
        DEATH = 'death', 'Death'
        PROPERTY = 'property', 'Property'
        INCOME_LOSS = 'income_loss', 'Income Loss'
    
    class StatusChoices(models.TextChoices):
        SUBMITTED = 'submitted', 'Submitted'
        UNDER_REVIEW = 'under_review', 'Under Review'
        INFO_REQUESTED = 'info_requested', 'Info Requested'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        PAID = 'paid', 'Paid'
    
    claim_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan_id = models.ForeignKey('plans.InsurancePlan', on_delete=models.PROTECT)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='claims')
    
    claim_type = models.CharField(
        max_length=50,
        choices=ClaimTypeChoices.choices
    )
    claim_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    description = models.TextField(
        validators=[MinLengthValidator(50)],
        help_text='Detailed description of the claim event (minimum 50 characters)'
    )
    
    # Documents
    documents = models.JSONField(default=list)  # Array of Azure Blob signed URLs
    
    # AI Verification
    ai_verification = models.JSONField(null=True, blank=True)
    ai_flagged = models.BooleanField(default=False)
    
    # Status and Review
    status = models.CharField(
        max_length=25,
        choices=StatusChoices.choices,
        default=StatusChoices.SUBMITTED
    )
    reviewed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_claims'
    )
    decision_reason = models.TextField(blank=True)
    
    # Payout
    payout_mpesa_ref = models.CharField(max_length=30, blank=True)
    
    # Blockchain
    blockchain_hash = models.CharField(max_length=66, blank=True)
    blockchain_tx = models.CharField(max_length=66, blank=True)
    
    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'claims_claim'
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['user_id', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['ai_flagged']),
        ]
    
    def __str__(self):
        return f"Claim {self.claim_id} - {self.user_id.full_name}"


class Notification(models.Model):
    """In-app notification for claim updates."""

    notification_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'claims_notification'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Notification for {self.recipient.full_name}"
