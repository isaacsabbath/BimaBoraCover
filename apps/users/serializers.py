"""
Serializers for users app.
"""

import re
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer as JWTTokenObtainPairSerializer
from .models import User
from .services.otp import generate_otp, send_otp_sms


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'national_id', 'phone_number',
            'role', 'is_active', 'kyc_status', 'kyc_verified_at', 'created_at'
        ]
        read_only_fields = [
            'id', 'is_active', 'kyc_status', 'kyc_verified_at', 'created_at'
        ]


class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for User model including KYC info."""
    
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
    
    class Meta:
        model = User
        fields = [
            'full_name', 'national_id', 'phone_number', 'email',
            'password', 'confirm_password', 'role'
        ]
    
    def validate_email(self, value):
        """Validate email uniqueness."""
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError('This email is already registered.')
        return value.lower()
    
    def validate_phone_number(self, value):
        """Validate phone number format."""
        if not re.match(r'^\+254\d{9}$', value):
            raise serializers.ValidationError(
                'Phone number must be in format +254XXXXXXXXX'
            )
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError('This phone number is already registered.')
        return value
    
    def validate_national_id(self, value):
        """Validate national ID uniqueness."""
        if User.objects.filter(national_id=value).exists():
            raise serializers.ValidationError('This national ID is already registered.')
        return value
    
    def validate(self, data):
        """Validate passwords match."""
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match.'
            })
        return data
    
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


class OTPVerifySerializer(serializers.Serializer):
    """Serializer for OTP verification."""
    
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6, min_length=6)
    
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
    
    def save(self):
        """Activate user after successful OTP verification."""
        user = self.validated_data['user']
        user.is_active = True
        user.otp_code = ''
        user.otp_created_at = None
        user.save()
        return user


class TokenObtainPairSerializer(JWTTokenObtainPairSerializer):
    """Custom JWT token serializer including role and kyc_status."""
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['email'] = user.email
        token['full_name'] = user.full_name
        token['role'] = user.role
        token['kyc_status'] = user.kyc_status
        
        return token


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request."""
    
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """Check if email exists."""
        if not User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError('Email not found.')
        return value.lower()


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
    
    def validate(self, data):
        """Validate passwords match."""
        if data.get('new_password') != data.get('confirm_password'):
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match.'
            })
        return data


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""
    
    class Meta:
        model = User
        fields = ['full_name', 'phone_number']
