"""
Models for insurance plans and policies.
"""

import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from apps.users.models import User


class InsurancePlan(models.Model):
    """Insurance plan catalogue."""
    
    class PlanTypeChoices(models.TextChoices):
        INDIVIDUAL = 'individual', 'Individual'
        FAMILY = 'family', 'Family'
        GROUP = 'group', 'Group'
    
    class CoverageCategoryChoices(models.TextChoices):
        HEALTH = 'health', 'Health'
        LIFE = 'life', 'Life'
        ACCIDENT = 'accident', 'Accident'
        PROPERTY = 'property', 'Property'
        INCOME_PROTECTION = 'income_protection', 'Income Protection'
    
    class PaymentFrequencyChoices(models.TextChoices):
        DAILY = 'daily', 'Daily'
        WEEKLY = 'weekly', 'Weekly'
        MONTHLY = 'monthly', 'Monthly'
        ANNUAL = 'annual', 'Annual'
    
    class StatusChoices(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        ARCHIVED = 'archived', 'Archived'
    
    plan_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan_name = models.CharField(max_length=200)
    plan_type = models.CharField(
        max_length=20,
        choices=PlanTypeChoices.choices
    )
    coverage_category = models.CharField(
        max_length=50,
        choices=CoverageCategoryChoices.choices
    )
    base_rate = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0.0001'))]
    )
    min_coverage = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    max_coverage = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    duration_days = models.IntegerField()
    payment_frequency = models.CharField(
        max_length=20,
        choices=PaymentFrequencyChoices.choices
    )
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE
    )
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'plans_insuranceplan'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'plan_type']),
            models.Index(fields=['coverage_category']),
        ]
    
    def __str__(self):
        return f"{self.plan_name} - {self.get_coverage_category_display()}"


class Policy(models.Model):
    """Active insurance policy for a user."""
    
    class StatusChoices(models.TextChoices):
        ACTIVE = 'active', 'Active'
        EXPIRED = 'expired', 'Expired'
        LAPSED = 'lapsed', 'Lapsed'
        CANCELLED = 'cancelled', 'Cancelled'
    
    policy_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='policies')
    plan_id = models.ForeignKey(InsurancePlan, on_delete=models.PROTECT)
    chama_id = models.ForeignKey(
        'chamas.Chama',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='policies'
    )
    coverage_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    premium_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    payment_reference = models.CharField(max_length=30)
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE
    )
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    blockchain_hash = models.CharField(max_length=66, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'plans_policy'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id', 'status']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Policy {self.policy_id} - {self.user_id.full_name}"
