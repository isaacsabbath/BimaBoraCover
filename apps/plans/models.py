# For beginners: This file (apps/plans/models.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

"""
Models for insurance plans and policies.
"""

import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from apps.users.models import User


# For beginners: This class 'InsurancePlan' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'InsurancePlan' groups related data and behavior
# so other parts of the app can use one structured object.
class InsurancePlan(models.Model):
    """Insurance plan catalogue."""
    
    # For beginners: This class 'PlanTypeChoices' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'PlanTypeChoices' groups related data and behavior
    # so other parts of the app can use one structured object.
    class PlanTypeChoices(models.TextChoices):
        INDIVIDUAL = 'individual', 'Individual'
        FAMILY = 'family', 'Family'
        GROUP = 'group', 'Group'
    
    # For beginners: This class 'CoverageCategoryChoices' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'CoverageCategoryChoices' groups related data and behavior
    # so other parts of the app can use one structured object.
    class CoverageCategoryChoices(models.TextChoices):
        HEALTH = 'health', 'Health'
        LIFE = 'life', 'Life'
        ACCIDENT = 'accident', 'Accident'
        PROPERTY = 'property', 'Property'
        INCOME_PROTECTION = 'income_protection', 'Income Protection'
    
    # For beginners: This class 'PaymentFrequencyChoices' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'PaymentFrequencyChoices' groups related data and behavior
    # so other parts of the app can use one structured object.
    class PaymentFrequencyChoices(models.TextChoices):
        DAILY = 'daily', 'Daily'
        WEEKLY = 'weekly', 'Weekly'
        MONTHLY = 'monthly', 'Monthly'
        ANNUAL = 'annual', 'Annual'
    
    # For beginners: This class 'StatusChoices' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'StatusChoices' groups related data and behavior
    # so other parts of the app can use one structured object.
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
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    class Meta:
        db_table = 'plans_insuranceplan'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'plan_type']),
            models.Index(fields=['coverage_category']),
        ]
    
    # For beginners: This function '__str__' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function '__str__' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def __str__(self):
        return f"{self.plan_name} - {self.get_coverage_category_display()}"


# For beginners: This class 'Policy' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'Policy' groups related data and behavior
# so other parts of the app can use one structured object.
class Policy(models.Model):
    """Active insurance policy for a user."""
    
    # For beginners: This class 'StatusChoices' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'StatusChoices' groups related data and behavior
    # so other parts of the app can use one structured object.
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
    payment_reference = models.CharField(max_length=100)
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
    
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    class Meta:
        db_table = 'plans_policy'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id', 'status']),
            models.Index(fields=['status']),
        ]
    
    # For beginners: This function '__str__' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function '__str__' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def __str__(self):
        return f"Policy {self.policy_id} - {self.user_id.full_name}"
