"""
Serializers for Payment transactions.
"""

from rest_framework import serializers
from apps.payments.models import Payment


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


class PaymentListSerializer(serializers.ModelSerializer):
    """Serializer for listing payments."""
    
    user_email = serializers.CharField(source='user_id.email', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'payment_id', 'user_email', 'amount', 'payment_type',
            'payment_direction', 'status', 'mpesa_ref', 'initiated_at'
        ]
        read_only_fields = [
            'payment_id', 'user_email', 'initiated_at'
        ]


class PaymentDetailSerializer(serializers.ModelSerializer):
    """Serializer for payment details."""
    
    user_email = serializers.CharField(source='user_id.email', read_only=True)
    plan_name = serializers.CharField(source='plan_id.plan_name', read_only=True, allow_null=True)
    
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


class PaymentCallbackSerializer(serializers.Serializer):
    """Serializer for M-Pesa callback data (for validation only)."""
    
    Body = serializers.DictField()
    
    def validate_Body(self, value):
        """Validate callback structure."""
        if 'stkCallback' not in value:
            raise serializers.ValidationError("Missing stkCallback in Body")
        return value
