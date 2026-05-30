"""
Models for Chama (savings group) management.
"""

import uuid
from django.db import models
from django.core.validators import MinValueValidator
from apps.users.models import User


class Chama(models.Model):
    """Chama (savings group) model."""
    
    class StatusChoices(models.TextChoices):
        ACTIVE = 'active', 'Active'
        SUSPENDED = 'suspended', 'Suspended'
        DISSOLVED = 'dissolved', 'Dissolved'
    
    chama_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group_name = models.CharField(max_length=200)
    registration_no = models.CharField(max_length=50, unique=True)
    admin_id = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='chamas_admin'
    )
    expected_members = models.IntegerField(validators=[MinValueValidator(2)])
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chamas_chama'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['admin_id']),
        ]
    
    def __str__(self):
        return f"{self.group_name} ({self.registration_no})"


class ChamaMember(models.Model):
    """Junction table for Chama membership."""
    
    class MemberRoleChoices(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        MEMBER = 'member', 'Member'
    
    class StatusChoices(models.TextChoices):
        ACTIVE = 'active', 'Active'
        LEFT = 'left', 'Left'
    
    membership_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chama_id = models.ForeignKey(Chama, on_delete=models.CASCADE, related_name='members')
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chama_memberships')
    member_role = models.CharField(
        max_length=20,
        choices=MemberRoleChoices.choices,
        default=MemberRoleChoices.MEMBER
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE
    )
    
    class Meta:
        db_table = 'chamas_chamember'
        unique_together = [('chama_id', 'user_id')]
        ordering = ['joined_at']
        indexes = [
            models.Index(fields=['chama_id', 'status']),
            models.Index(fields=['user_id']),
        ]
    
    def __str__(self):
        return f"{self.user_id.full_name} - {self.chama_id.group_name}"
