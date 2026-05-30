"""
User model for Bima Afya.
"""

import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.validators import MinLengthValidator


class UserManager(BaseUserManager):
    """Manager for User model."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user."""
        if not email:
            raise ValueError('Email is required')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'super_admin')
        extra_fields.setdefault('is_active', True)
        
        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model using email as login credential."""
    
    class RoleChoices(models.TextChoices):
        SUPER_ADMIN = 'super_admin', 'Super Admin'
        CLAIMS_OFFICER = 'claims_officer', 'Claims Officer'
        CHAMA_ADMIN = 'chama_admin', 'Chama Admin'
        CHAMA_MEMBER = 'chama_member', 'Chama Member'
        INDIVIDUAL = 'individual', 'Individual'
    
    class KYCStatusChoices(models.TextChoices):
        PENDING = 'pending', 'Pending'
        VERIFIED = 'verified', 'Verified'
        FLAGGED = 'flagged', 'Flagged'
        REVIEW = 'review', 'Needs Review'
        REJECTED = 'rejected', 'Rejected'
    
    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Authentication
    email = models.EmailField(unique=True, max_length=254)
    
    # Profile
    full_name = models.CharField(max_length=150, validators=[MinLengthValidator(2)])
    national_id = models.CharField(max_length=20, unique=True)
    phone_number = models.CharField(max_length=15, unique=True)
    
    # System
    role = models.CharField(
        max_length=30,
        choices=RoleChoices.choices,
        default=RoleChoices.INDIVIDUAL
    )
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    
    # KYC Status (for manual claims officer review, GCP automatic processing removed)
    kyc_status = models.CharField(
        max_length=20,
        choices=KYCStatusChoices.choices,
        default=KYCStatusChoices.PENDING
    )
    kyc_verification_result = models.JSONField(null=True, blank=True)
    kyc_verified_at = models.DateTimeField(null=True, blank=True)
    
    # OTP
    otp_code = models.CharField(max_length=6, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Manager
    objects = UserManager()
    
    # Configuration
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'national_id', 'phone_number']
    
    class Meta:
        db_table = 'users_user'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['kyc_status']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        return f"{self.full_name} ({self.email})"
    
    def has_kyc_verified(self):
        """Check if user has verified KYC."""
        return self.kyc_status == self.KYCStatusChoices.VERIFIED
