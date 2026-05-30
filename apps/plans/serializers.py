"""
Serializers for Insurance Plans and Policies.
"""

from rest_framework import serializers
from decimal import Decimal
from apps.plans.models import InsurancePlan, Policy
from apps.plans.services.premium_calculator import calculate_premium, calculate_group_discount


class PremiumCalculationSerializer(serializers.Serializer):
    """Serializer for premium calculation request/response."""
    
    coverage_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    duration_days = serializers.IntegerField(min_value=1)
    group_size = serializers.IntegerField(min_value=1, default=1)
    payment_frequency = serializers.ChoiceField(
        choices=['daily', 'weekly', 'monthly', 'annual'],
        default='monthly'
    )
    
    # Response fields (read-only)
    base_premium = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    group_discount_percent = serializers.IntegerField(read_only=True)
    discount_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    final_premium = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )


class InsurancePlanListSerializer(serializers.ModelSerializer):
    """Serializer for listing insurance plans (minimal data)."""
    
    class Meta:
        model = InsurancePlan
        fields = [
            'plan_id', 'plan_name', 'plan_type', 'coverage_category',
            'base_rate', 'min_coverage', 'max_coverage', 'status'
        ]


class InsurancePlanDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed plan view with full information."""
    
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = InsurancePlan
        fields = [
            'plan_id', 'plan_name', 'plan_type', 'coverage_category',
            'base_rate', 'min_coverage', 'max_coverage', 'duration_days',
            'payment_frequency', 'status', 'description', 'created_by',
            'created_by_name', 'created_at'
        ]
        read_only_fields = ['plan_id', 'created_by', 'created_at']


class InsurancePlanCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating insurance plans (admin only)."""
    
    class Meta:
        model = InsurancePlan
        fields = [
            'plan_name', 'plan_type', 'coverage_category',
            'base_rate', 'min_coverage', 'max_coverage', 'duration_days',
            'payment_frequency', 'status', 'description'
        ]
    
    def create(self, validated_data):
        """Auto-set created_by to current user."""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class PolicySerializer(serializers.ModelSerializer):
    """Serializer for Policy (insurance contract)."""
    
    plan_name = serializers.CharField(source='plan_id.plan_name', read_only=True)
    user_email = serializers.CharField(source='user_id.email', read_only=True)
    
    class Meta:
        model = Policy
        fields = [
            'policy_id', 'user_id', 'user_email', 'plan_id', 'plan_name',
            'chama_id', 'coverage_amount', 'premium_paid', 'payment_reference',
            'status', 'start_date', 'end_date', 'blockchain_hash', 'created_at'
        ]
        read_only_fields = [
            'policy_id', 'user_id', 'blockchain_hash', 'created_at'
        ]
