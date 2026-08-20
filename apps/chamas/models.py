# For beginners: This file (apps/chamas/models.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

"""
Models for Chama (savings group) management.
"""

import uuid
from django.db import models
from django.core.validators import MinValueValidator
from apps.users.models import User


# For beginners: This class 'Chama' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'Chama' groups related data and behavior
# so other parts of the app can use one structured object.
class Chama(models.Model):
    """Chama (savings group) model."""
    
    # For beginners: This class 'StatusChoices' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'StatusChoices' groups related data and behavior
    # so other parts of the app can use one structured object.
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
    
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    class Meta:
        db_table = 'chamas_chama'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['admin_id']),
        ]
    
    # For beginners: This function '__str__' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function '__str__' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def __str__(self):
        return f"{self.group_name} ({self.registration_no})"


# For beginners: This class 'ChamaMember' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'ChamaMember' groups related data and behavior
# so other parts of the app can use one structured object.
class ChamaMember(models.Model):
    """Junction table for Chama membership."""
    
    # For beginners: This class 'MemberRoleChoices' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'MemberRoleChoices' groups related data and behavior
    # so other parts of the app can use one structured object.
    class MemberRoleChoices(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        MEMBER = 'member', 'Member'
    
    # For beginners: This class 'StatusChoices' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'StatusChoices' groups related data and behavior
    # so other parts of the app can use one structured object.
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
    
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    class Meta:
        db_table = 'chamas_chamember'
        unique_together = [('chama_id', 'user_id')]
        ordering = ['joined_at']
        indexes = [
            models.Index(fields=['chama_id', 'status']),
            models.Index(fields=['user_id']),
        ]
    
    # For beginners: This function '__str__' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function '__str__' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def __str__(self):
        return f"{self.user_id.full_name} - {self.chama_id.group_name}"
