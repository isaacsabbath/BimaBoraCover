# For beginners: This file (apps/payments/serializers.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

"""
Serializers for Payment transactions.
"""

from rest_framework import serializers
from apps.payments.models import Payment


# For beginners: This class 'PaymentInitiateSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'PaymentInitiateSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
class PaymentInitiateSerializer(serializers.Serializer):
    """Initiate STK push payment."""
    
    phone_number = serializers.CharField(
        max_length=15,
        help_text="Phone number in format 07XXXXXXXX or 254XXXXXXXXX"
    )
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=1,
        help_text="Amount in KES"
    )
    plan_id = serializers.UUIDField(required=False, allow_null=True)
    
    # For beginners: This function 'validate_phone_number' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'validate_phone_number' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def validate_phone_number(self, value):
        """Validate Kenyan phone number format."""
        value = value.strip().replace(' ', '').replace('-', '')

        if value.startswith('+254'):
            value = value[1:]

        if value.startswith('07'):
            value = '254' + value[1:]

        if not value.startswith('254'):
            raise serializers.ValidationError("Phone must start with 07 or 254")
        if len(value) != 12:
            raise serializers.ValidationError("Phone must be exactly 12 digits after normalization")
        return value


# For beginners: This class 'PaymentListSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'PaymentListSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
class PaymentListSerializer(serializers.ModelSerializer):
    """Serializer for listing payments."""
    
    user_email = serializers.CharField(source='user_id.email', read_only=True)
    
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    class Meta:
        model = Payment
        fields = [
            'payment_id', 'user_email', 'amount', 'payment_type',
            'payment_direction', 'status', 'mpesa_ref', 'initiated_at'
        ]
        read_only_fields = [
            'payment_id', 'user_email', 'initiated_at'
        ]


# For beginners: This class 'PaymentDetailSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'PaymentDetailSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
class PaymentDetailSerializer(serializers.ModelSerializer):
    """Serializer for payment details."""
    
    user_email = serializers.CharField(source='user_id.email', read_only=True)
    plan_name = serializers.CharField(source='plan_id.plan_name', read_only=True, allow_null=True)
    
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    class Meta:
        model = Payment
        fields = [
            'payment_id', 'user_id', 'user_email', 'plan_id', 'plan_name',
            'chama_id', 'amount', 'payment_type', 'payment_direction',
            'mpesa_ref', 'status', 'failure_reason', 'initiated_at',
            'confirmed_at'
        ]
        read_only_fields = [
            'payment_id', 'user_id', 'initiated_at', 'confirmed_at'
        ]


# For beginners: This class 'PaymentCallbackSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'PaymentCallbackSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
class PaymentCallbackSerializer(serializers.Serializer):
    """Serializer for M-Pesa callback data (for validation only)."""
    
    Body = serializers.DictField()
    
    # For beginners: This function 'validate_Body' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'validate_Body' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def validate_Body(self, value):
        """Validate callback structure."""
        if 'stkCallback' not in value:
            raise serializers.ValidationError("Missing stkCallback in Body")
        return value
