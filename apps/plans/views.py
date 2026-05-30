"""
Views for Insurance Plans browsing and premium calculation.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import OrderingFilter

from apps.plans.models import InsurancePlan, Policy
from apps.plans.serializers import (
    InsurancePlanListSerializer, InsurancePlanDetailSerializer,
    InsurancePlanCreateUpdateSerializer, PolicySerializer,
    PremiumCalculationSerializer
)
from apps.users.permissions import IsSuperAdmin
from apps.plans.services.premium_calculator import calculate_premium, calculate_group_discount


class InsurancePlanViewSet(viewsets.ModelViewSet):
    """ViewSet for browsing and managing insurance plans."""
    
    permission_classes = [IsAuthenticated]
    lookup_field = 'plan_id'
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return InsurancePlanListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return InsurancePlanCreateUpdateSerializer
        elif self.action == 'calculate_premium':
            return PremiumCalculationSerializer
        else:
            return InsurancePlanDetailSerializer
    
    def get_queryset(self):
        """Return active plans (or all for admin)."""
        if self.request.user.role == 'super_admin':
            return InsurancePlan.objects.all().order_by('-created_at')
        return InsurancePlan.objects.filter(status='active').order_by('-created_at')
    
    def get_permissions(self):
        """Admin actions require IsSuperAdmin."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsSuperAdmin]
        return super().get_permissions()
    
    def create(self, request, *args, **kwargs):
        """Create new plan (super_admin only)."""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def calculate_premium(self, request, plan_id=None):
        """Calculate premium for given plan and parameters."""
        plan = self.get_object()
        
        serializer = PremiumCalculationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            base_premium = calculate_premium(
                base_rate=plan.base_rate,
                coverage_amount=serializer.validated_data['coverage_amount'],
                duration_days=serializer.validated_data['duration_days'],
                group_size=serializer.validated_data.get('group_size', 1),
                payment_frequency=serializer.validated_data.get('payment_frequency', 'monthly')
            )
            
            group_size = serializer.validated_data.get('group_size', 1)
            discount_data = calculate_group_discount(base_premium, group_size)
            
            return Response({
                'plan_id': str(plan_id),
                'plan_name': plan.plan_name,
                'coverage_amount': serializer.validated_data['coverage_amount'],
                'duration_days': serializer.validated_data['duration_days'],
                'group_size': group_size,
                'payment_frequency': serializer.validated_data.get('payment_frequency', 'monthly'),
                'base_premium': str(base_premium),
                'group_discount_percent': discount_data['discount_percent'],
                'discount_amount': str(discount_data['discount_amount']),
                'final_premium': str(discount_data['final_premium'])
            }, status=status.HTTP_200_OK)
        
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get plans filtered by type."""
        plan_type = request.query_params.get('type')
        if not plan_type:
            return Response(
                {'error': 'Plan type parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        plans = self.get_queryset().filter(plan_type=plan_type)
        serializer = self.get_serializer(plans, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get plans filtered by coverage category."""
        category = request.query_params.get('category')
        if not category:
            return Response(
                {'error': 'Coverage category parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        plans = self.get_queryset().filter(coverage_category=category)
        serializer = self.get_serializer(plans, many=True)
        return Response(serializer.data)


class PolicyViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing policies (read-only; creation via payments)."""
    
    permission_classes = [IsAuthenticated]
    serializer_class = PolicySerializer
    lookup_field = 'policy_id'
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return user's policies."""
        return Policy.objects.filter(user_id=self.request.user).order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get user's active policies."""
        from django.utils import timezone
        today = timezone.now().date()
        
        policies = self.get_queryset().filter(
            status='active',
            start_date__lte=today,
            end_date__gte=today
        )
        serializer = self.get_serializer(policies, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get user's policy history (all statuses)."""
        policies = self.get_queryset()
        serializer = self.get_serializer(policies, many=True)
        return Response(serializer.data)


# ─── Template Views ───────────────────────────────────────────────────────────

@login_required(login_url='login')
def explore_page(request):
    plan_types = [
        {'key': 'individual', 'label': 'Individual'},
        {'key': 'family', 'label': 'Family'},
        {'key': 'group', 'label': 'Group'},
    ]
    tabs = []
    for pt in plan_types:
        tabs.append({
            'key': pt['key'],
            'label': pt['label'],
            'plans': InsurancePlan.objects.filter(plan_type=pt['key'], status='active'),
        })
    return render(request, 'plans/list.html', {'tabs': tabs})


@login_required(login_url='login')
def plan_detail_page(request, plan_id):
    plan = get_object_or_404(InsurancePlan, plan_id=plan_id, status='active')
    return render(request, 'plans/detail.html', {'plan': plan})


@login_required(login_url='login')
def select_plan_page(request, plan_id):
    plan = get_object_or_404(InsurancePlan, plan_id=plan_id)
    messages.success(request, f'You selected {plan.plan_name}. Complete payment to activate.')
    return redirect('payment')
