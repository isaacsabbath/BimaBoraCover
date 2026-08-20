# For beginners: This file (apps/users/models.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

"""
=================================================
USER MODEL & KYC DOCUMENT MODEL
=================================================

This file defines two core database models for the BimaBora insurance platform:

1. **User** — The custom user model that replaces Django's default.
   Every person who uses the platform (individual customers, chama admins,
   claims officers, and super admins) is represented here. It uses
   email as the login identifier instead of a username.

2. **KYCDocument** — Tracks identity documents (national ID, passport,
   driver's license) uploaded by users during Know-Your-Customer (KYC)
   verification. Each document goes through: PENDING -> UPLOADED -> ANALYZED
   (or FAILED), and the analysis result from Azure Document Intelligence
   is stored here.

DEPENDENCIES:
    - Django's auth framework (AbstractBaseUser, PermissionsMixin)
    - UUID generation for primary keys

RELATIONSHIPS:
    - User has many KYCDocument records (one-to-many via ForeignKey)
    - User has many Policy records (defined in apps.plans.models)
    - User has many Claim records (defined in apps.claims.models)
    - User has many Payment records (defined in apps.payments.models)
"""

import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.validators import MinLengthValidator


# ============================================================================
# CUSTOM USER MANAGER
# ============================================================================
# This manager is how User objects get created. It sits between your code
# and the database, providing create_user() and create_superuser() helpers.
# Django expects every custom user model to have a corresponding manager.
# ============================================================================

# For beginners: This class 'UserManager' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'UserManager' groups related data and behavior
# so other parts of the app can use one structured object.
class UserManager(BaseUserManager):
    """
    Manager for creating User instances.

    Why this exists: Django's default UserManager assumes a username field,
    but we use email as the login identifier, so we need this custom manager
    to handle account creation properly.

    Lifecycle:
        create_user()  -> called when a regular person registers
        create_superuser() -> called via `python manage.py createsuperuser`
    """

    # For beginners: This function 'create_user' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'create_user' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a regular (non-admin) user account.

        What happens:
            1. Validates that an email was provided (required for login).
            2. Normalizes the email (lowercases the domain part).
            3. Creates the User model instance with all provided fields.
            4. Hashes the password so it's never stored in plain text.
            5. Saves to the database using the default database connection.

        Parameters:
            email (str): The user's email address (becomes the login ID).
            password (str, optional): Raw password (will be hashed). Can be
                None for auto-generated accounts (e.g., claims officers).
            extra_fields (dict): Any additional User model fields like
                full_name, phone_number, national_id, role, etc.

        Returns:
            User: The newly created user instance (already saved to DB).

        Raises:
            ValueError: If no email is provided.

        Edge cases:
            - If password is None, the user cannot log in with a password
              (they'd need a password reset or OTP-based flow).
        """
        if not email:
            raise ValueError('Email is required')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    # For beginners: This function 'create_superuser' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'create_superuser' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a superuser (full admin access).

        What happens:
            1. Sets default admin flags: is_staff=True (Django admin access),
               is_superuser=True (all permissions), role='super_admin'.
            2. Forces is_active=True so the admin can log in immediately.
            3. Validates that the critical flags are actually set.
            4. Delegates to create_user() to handle the rest.

        Parameters:
            email (str): Superuser's email (login ID).
            password (str, optional): Raw password for the superuser.
            extra_fields (dict): Any additional fields to set.

        Returns:
            User: The newly created superuser instance.

        Raises:
            ValueError: If is_staff or is_superuser were somehow not set
                (e.g., someone passed is_staff=False explicitly).

        Note:
            The setdefault() calls above mean the caller CAN override these
            defaults if they really want to, but there's a safety check below.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'super_admin')
        extra_fields.setdefault('is_active', True)

        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True')

        return self.create_user(email, password, **extra_fields)


# ============================================================================
# CUSTOM USER MODEL
# ============================================================================
# This replaces Django's built-in User model. The key change is that we use
# email as the unique identifier for login instead of a username.
# We also add fields for KYC verification, OTP-based activation, and role-
# based access control (RBAC) that the application depends on.
# ============================================================================

# For beginners: This class 'User' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'User' groups related data and behavior
# so other parts of the app can use one structured object.
class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model using email as the login credential (not username).

    What this model stores:
        - Authentication: email (login ID), password (hashed)
        - Profile: full_name, national_id, phone_number
        - Role: Controls what the user can do (super_admin, claims_officer,
          chama_admin, chama_member, individual)
        - KYC: Status of identity verification (pending/verified/flagged/rejected)
        - OTP: One-time password for phone-based activation

    Why custom instead of Django's default User:
        - We need email-only login (no username field).
        - We need role-based access control (Django groups alone are too complex).
        - We need KYC status tracking built into the user record.
        - We need phone-based OTP activation before the account is active.

    Who uses this model:
        - Nearly every other model in the project references User via ForeignKey.
        - Authentication system (login, JWT tokens, password reset).
        - KYC verification pipeline.
        - Claims workflow (claim.user_id, claim.reviewed_by).
    """

    # ==========================================================================
    # ROLE CHOICES
    # ==========================================================================
    # These define what actions a user is allowed to perform.
    # The roles form a rough hierarchy, but each has unique capabilities:
    #   super_admin     - Full system access, can create claims officers
    #   claims_officer  - Reviews claims and KYC documents
    #   chama_admin     - Manages a savings group (Chama)
    #   chama_member    - Member of a savings group
    #   individual      - Regular insurance customer
    # ==========================================================================

    # For beginners: This class 'RoleChoices' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'RoleChoices' groups related data and behavior
    # so other parts of the app can use one structured object.
    class RoleChoices(models.TextChoices):
        SUPER_ADMIN = 'super_admin', 'Super Admin'
        CLAIMS_OFFICER = 'claims_officer', 'Claims Officer'
        CHAMA_ADMIN = 'chama_admin', 'Chama Admin'
        CHAMA_MEMBER = 'chama_member', 'Chama Member'
        INDIVIDUAL = 'individual', 'Individual'

    # ==========================================================================
    # KYC STATUS CHOICES
    # ==========================================================================
    # KYC (Know Your Customer) is the process of verifying a user's identity
    # by analyzing their uploaded ID documents. These statuses track where
    # the user is in that process.
    #   pending  - No KYC verification attempted yet
    #   verified - Identity successfully verified (can access all features)
    #   flagged  - AI detected potential issues (e.g., expired ID, mismatch)
    #   review   - Needs manual review by a claims officer
    #   rejected - Identity verification failed
    # ==========================================================================

    # For beginners: This class 'KYCStatusChoices' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'KYCStatusChoices' groups related data and behavior
    # so other parts of the app can use one structured object.
    class KYCStatusChoices(models.TextChoices):
        PENDING = 'pending', 'Pending'
        VERIFIED = 'verified', 'Verified'
        FLAGGED = 'flagged', 'Flagged'
        REVIEW = 'review', 'Needs Review'
        REJECTED = 'rejected', 'Rejected'

    # ==========================================================================
    # DATABASE FIELDS
    # ==========================================================================

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField(unique=True, max_length=254)

    full_name = models.CharField(max_length=150, validators=[MinLengthValidator(2)])
    national_id = models.CharField(max_length=20, unique=True)
    phone_number = models.CharField(max_length=15, unique=True)

    role = models.CharField(
        max_length=30,
        choices=RoleChoices.choices,
        default=RoleChoices.INDIVIDUAL
    )
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    kyc_status = models.CharField(
        max_length=20,
        choices=KYCStatusChoices.choices,
        default=KYCStatusChoices.PENDING
    )
    kyc_verification_result = models.JSONField(null=True, blank=True)
    kyc_verified_at = models.DateTimeField(null=True, blank=True)

    otp_code = models.CharField(max_length=6, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'national_id', 'phone_number']

    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    class Meta:
        db_table = 'users_user'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['kyc_status']),
            models.Index(fields=['role']),
        ]

    # For beginners: This function '__str__' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function '__str__' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def __str__(self):
        return f"{self.full_name} ({self.email})"

    # For beginners: This function 'has_kyc_verified' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'has_kyc_verified' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def has_kyc_verified(self):
        return self.kyc_status == self.KYCStatusChoices.VERIFIED


# ============================================================================
# KYC DOCUMENT MODEL
# ============================================================================
# Each time a user uploads an ID document for verification, a KYCDocument
# record is created. The document goes through stages:
#   1. PENDING  - Record created, file not yet uploaded to cloud storage
#   2. UPLOADED - File successfully uploaded to Azure Blob Storage
#   3. ANALYZED - Azure Document Intelligence has processed the document
#   4. FAILED   - Upload or analysis encountered an error
#
# The analysis_result field stores the complete output from Azure, including
# extracted fields (name, ID number, DOB) and their confidence scores.
# ============================================================================

# For beginners: This class 'KYCDocument' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'KYCDocument' groups related data and behavior
# so other parts of the app can use one structured object.
class KYCDocument(models.Model):
    """
    Tracks uploaded KYC identity documents and their AI analysis results.

    Why this model exists:
        - Each document goes through multiple processing stages (upload, AI
          analysis). We need to track the state at each stage.
        - The analysis result needs to be stored for auditing and potential
          manual review.
        - A user may upload multiple documents (e.g., national ID + passport).

    Lifecycle:
        1. User uploads a file via the API.
        2. A KYCDocument record is created with status=PENDING.
        3. The file is uploaded to Azure Blob Storage -> status=UPLOADED.
        4. Azure Document Intelligence analyzes the image -> status=ANALYZED.
        5. If any step fails -> status=FAILED.

    Relationships:
        - user -> User (the person who owns this document)
        - The User's kyc_status and kyc_verification_result are updated based
          on this document's analysis.
    """

    # For beginners: This class 'DocumentTypeChoices' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'DocumentTypeChoices' groups related data and behavior
    # so other parts of the app can use one structured object.
    class DocumentTypeChoices(models.TextChoices):
        NATIONAL_ID = 'national_id', 'National ID'
        PASSPORT = 'passport', 'Passport'
        DRIVERS_LICENSE = 'drivers_license', "Driver's License"

    # For beginners: This class 'UploadStatusChoices' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'UploadStatusChoices' groups related data and behavior
    # so other parts of the app can use one structured object.
    class UploadStatusChoices(models.TextChoices):
        PENDING = 'pending', 'Pending Upload'
        UPLOADED = 'uploaded', 'Uploaded to Storage'
        ANALYZED = 'analyzed', 'Analysis Complete'
        FAILED = 'failed', 'Upload/Analysis Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kyc_documents')

    document_type = models.CharField(
        max_length=30,
        choices=DocumentTypeChoices.choices,
        default=DocumentTypeChoices.NATIONAL_ID
    )

    uploaded_file = models.FileField(
        upload_to='kyc-documents/%Y/%m/%d/',
        help_text='Uploaded KYC document file'
    )

    document_url = models.URLField(
        blank=True,
        null=True,
        help_text='Azure Blob Storage URL after upload'
    )

    upload_status = models.CharField(
        max_length=20,
        choices=UploadStatusChoices.choices,
        default=UploadStatusChoices.PENDING
    )

    analysis_result = models.JSONField(
        null=True,
        blank=True,
        help_text='Complete analysis result from Azure Document Intelligence'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uploaded_at = models.DateTimeField(null=True, blank=True)
    analyzed_at = models.DateTimeField(null=True, blank=True)

    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    class Meta:
        db_table = 'users_kyc_document'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['upload_status']),
        ]

    # For beginners: This function '__str__' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function '__str__' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def __str__(self):
        return f"{self.user.email} - {self.document_type} ({self.upload_status})"