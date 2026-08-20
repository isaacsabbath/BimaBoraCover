# For beginners: This file (apps/plans/serializers.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

"""
Serializers for Insurance Plans and Policies.
"""

from rest_framework import serializers
from decimal import Decimal
from apps.plans.models import InsurancePlan, Policy
from apps.plans.services.premium_calculator import calculate_premium, calculate_group_discount


# For beginners: This class 'PremiumCalculationSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'PremiumCalculationSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
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


# For beginners: This class 'InsurancePlanListSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'InsurancePlanListSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
class InsurancePlanListSerializer(serializers.ModelSerializer):
    """Serializer for listing insurance plans (minimal data)."""
    
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    class Meta:
        model = InsurancePlan
        fields = [
            'plan_id', 'plan_name', 'plan_type', 'coverage_category',
            'base_rate', 'min_coverage', 'max_coverage', 'status'
        ]


# For beginners: This class 'InsurancePlanDetailSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'InsurancePlanDetailSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
class InsurancePlanDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed plan view with full information."""
    
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    class Meta:
        model = InsurancePlan
        fields = [
            'plan_id', 'plan_name', 'plan_type', 'coverage_category',
            'base_rate', 'min_coverage', 'max_coverage', 'duration_days',
            'payment_frequency', 'status', 'description', 'created_by',
            'created_by_name', 'created_at'
        ]
        read_only_fields = ['plan_id', 'created_by', 'created_at']


# For beginners: This class 'InsurancePlanCreateUpdateSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'InsurancePlanCreateUpdateSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
class InsurancePlanCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating insurance plans (admin only)."""
    
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    class Meta:
        model = InsurancePlan
        fields = [
            'plan_name', 'plan_type', 'coverage_category',
            'base_rate', 'min_coverage', 'max_coverage', 'duration_days',
            'payment_frequency', 'status', 'description'
        ]
    
    # For beginners: This function 'create' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'create' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def create(self, validated_data):
        """Auto-set created_by to current user."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        return super().create(validated_data)


# For beginners: This class 'PolicySerializer' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'PolicySerializer' groups related data and behavior
# so other parts of the app can use one structured object.
class PolicySerializer(serializers.ModelSerializer):
    """Serializer for Policy (insurance contract)."""
    
    plan_name = serializers.CharField(source='plan_id.plan_name', read_only=True)
    user_email = serializers.CharField(source='user_id.email', read_only=True)
    
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
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
