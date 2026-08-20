# For beginners: This file (apps/users/serializers.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

"""
Serializers for users app.
"""

import re
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer as JWTTokenObtainPairSerializer
from .models import User
from .services.otp import generate_otp, send_otp_sms


# For beginners: This class 'UserSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'UserSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'national_id', 'phone_number',
            'role', 'is_active', 'kyc_status', 'kyc_verified_at', 'created_at'
        ]
        read_only_fields = [
            'id', 'is_active', 'kyc_status', 'kyc_verified_at', 'created_at'
        ]


# For beginners: This class 'UserDetailSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'UserDetailSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for User model including KYC info."""
    
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'national_id', 'phone_number',
            'role', 'is_active', 'kyc_status', 'kyc_verification_result',
            'kyc_verified_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'kyc_verification_result', 'kyc_verified_at', 'created_at', 'updated_at'
        ]


# For beginners: This class 'RegisterSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'RegisterSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
        help_text='Minimum 8 characters'
    )
    confirm_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    class Meta:
        model = User
        fields = [
            'full_name', 'national_id', 'phone_number', 'email',
            'password', 'confirm_password', 'role'
        ]
    
    # For beginners: This function 'validate_email' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'validate_email' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def validate_email(self, value):
        """Validate email uniqueness."""
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError('This email is already registered.')
        return value.lower()
    
    # For beginners: This function 'validate_phone_number' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'validate_phone_number' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def validate_phone_number(self, value):
        """Validate phone number format."""
        value = value.strip().replace(' ', '').replace('-', '')

        if value.startswith('+254'):
            value = value[1:]

        if value.startswith('07'):
            value = '254' + value[1:]

        if not re.match(r'^254\d{9}$', value):
            raise serializers.ValidationError(
                'Phone number must be in format 07XXXXXXXX or 254XXXXXXXXX'
            )
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError('This phone number is already registered.')
        return value
    
    # For beginners: This function 'validate_national_id' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'validate_national_id' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def validate_national_id(self, value):
        """Validate national ID uniqueness."""
        if User.objects.filter(national_id=value).exists():
            raise serializers.ValidationError('This national ID is already registered.')
        return value
    
    # For beginners: This function 'validate' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'validate' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def validate(self, data):
        """Validate passwords match."""
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match.'
            })
        return data
    
    # For beginners: This function 'create' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'create' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def create(self, validated_data):
        """Create user and send OTP."""
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        
        user = User(**validated_data)
        user.set_password(password)
        user.is_active = False  # Not active until OTP verified
        
        # Generate and send OTP
        otp = generate_otp()
        user.otp_code = otp
        user.otp_created_at = timezone.now()
        
        user.save()
        
        # Send OTP via SMS in background
        try:
            send_otp_sms(user.phone_number, otp)
        except Exception as e:
            # Log error but don't fail registration
            print(f"Failed to send OTP SMS: {e}")
        
        return user


# For beginners: This class 'OTPVerifySerializer' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'OTPVerifySerializer' groups related data and behavior
# so other parts of the app can use one structured object.
class OTPVerifySerializer(serializers.Serializer):
    """Serializer for OTP verification."""
    
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6, min_length=6)
    
    # For beginners: This function 'validate' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'validate' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def validate(self, data):
        """Validate OTP matches user and hasn't expired."""
        try:
            user = User.objects.get(email=data['email'].lower())
        except User.DoesNotExist:
            raise serializers.ValidationError('Invalid email or OTP.')
        
        # Check OTP validity
        if user.otp_code != data['otp_code']:
            raise serializers.ValidationError('Invalid email or OTP.')
        
        # Check OTP expiry (10 minutes)
        if not user.otp_created_at:
            raise serializers.ValidationError('OTP expired. Please register again.')
        
        from datetime import timedelta
        expiry = user.otp_created_at + timedelta(minutes=10)
        if timezone.now() > expiry:
            raise serializers.ValidationError('OTP expired. Please request a new one.')
        
        data['user'] = user
        return data
    
    # For beginners: This function 'save' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'save' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def save(self):
        """Activate user after successful OTP verification."""
        user = self.validated_data['user']
        user.is_active = True
        user.otp_code = ''
        user.otp_created_at = None
        user.save()
        return user


# For beginners: This class 'TokenObtainPairSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'TokenObtainPairSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
class TokenObtainPairSerializer(JWTTokenObtainPairSerializer):
    """Custom JWT token serializer including role and kyc_status."""
    
    @classmethod
    # For beginners: This function 'get_token' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'get_token' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['email'] = user.email
        token['full_name'] = user.full_name
        token['role'] = user.role
        token['kyc_status'] = user.kyc_status
        
        return token


# For beginners: This class 'PasswordResetRequestSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'PasswordResetRequestSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request."""
    
    email = serializers.EmailField()
    
    # For beginners: This function 'validate_email' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'validate_email' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def validate_email(self, value):
        """Check if email exists."""
        if not User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError('Email not found.')
        return value.lower()


# For beginners: This class 'PasswordResetConfirmSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'PasswordResetConfirmSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation."""
    
    token = serializers.CharField()
    new_password = serializers.CharField(
        min_length=8,
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        style={'input_type': 'password'}
    )
    
    # For beginners: This function 'validate' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'validate' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def validate(self, data):
        """Validate passwords match."""
        if data.get('new_password') != data.get('confirm_password'):
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match.'
            })
        return data


# For beginners: This class 'ProfileUpdateSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'ProfileUpdateSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""
    
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    class Meta:
        model = User
        fields = ['full_name', 'phone_number']


# For beginners: This class 'KYCDocumentSubmitSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'KYCDocumentSubmitSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
class KYCDocumentSubmitSerializer(serializers.Serializer):
    """Serializer for uploading and submitting KYC documents."""
    
    document_file = serializers.FileField(
        help_text='ID document image (PNG, JPG, PDF - max 10MB)'
    )
    document_type = serializers.ChoiceField(
        choices=['national_id', 'passport', 'drivers_license'],
        default='national_id',
        help_text='Type of ID document being submitted'
    )
    
    # For beginners: This function 'validate_document_file' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'validate_document_file' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def validate_document_file(self, value):
        """Validate file size and type."""
        # Check file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f'File size must not exceed 10MB. Current size: {value.size / 1024 / 1024:.2f}MB'
            )
        
        # Check file type
        allowed_extensions = ['jpg', 'jpeg', 'png', 'pdf', 'tiff', 'bmp']
        filename = value.name.lower()
        ext = filename.split('.')[-1] if '.' in filename else ''
        
        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                f'File type not allowed. Allowed types: {", ".join(allowed_extensions)}'
            )
        
        return value


# For beginners: This class 'KYCVerificationResultSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'KYCVerificationResultSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
class KYCVerificationResultSerializer(serializers.Serializer):
    """Serializer for KYC verification results."""
    
    verified = serializers.BooleanField()
    flags = serializers.ListField(
        child=serializers.CharField(),
        help_text='List of flags raised (e.g., ID_EXPIRED, LOW_CONFIDENCE)'
    )
    mismatches = serializers.ListField(
        child=serializers.DictField(),
        help_text='List of mismatches between extracted and registered data'
    )
    confidence_score = serializers.FloatField(
        help_text='Average confidence score from document analysis (0-1)'
    )
    
    
# For beginners: This class 'KYCAnalysisDetailSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'KYCAnalysisDetailSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
class KYCAnalysisDetailSerializer(serializers.Serializer):
    """Detailed serializer for KYC analysis response."""
    
    success = serializers.BooleanField()
    error = serializers.CharField(required=False, allow_blank=True)
    extracted_data = serializers.DictField(required=False)
    verification_result = KYCVerificationResultSerializer(required=False)
    summary = serializers.CharField(
        required=False,
        help_text='Human-readable summary of extracted information'
    )


# For beginners: This class 'KYCDocumentDetailSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'KYCDocumentDetailSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
class KYCDocumentDetailSerializer(serializers.Serializer):
    """Serializer for KYC document details."""
    
    id = serializers.CharField()
    document_type = serializers.CharField()
    upload_status = serializers.CharField()
    document_url = serializers.URLField(required=False)
    analysis_result = serializers.DictField(required=False)
    created_at = serializers.DateTimeField()
    uploaded_at = serializers.DateTimeField(required=False)
    analyzed_at = serializers.DateTimeField(required=False)
