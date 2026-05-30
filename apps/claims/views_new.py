"""
Views for Insurance Claims workflow.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
import logging

from apps.claims.models import Claim
from apps.claims.serializers_new import (
    ClaimListSerializer, ClaimDetailSerializer,
    ClaimSubmitSerializer, ClaimReviewSerializer
)
from apps.users.permissions import IsClaimsOfficer
from apps.payments.services.daraja import DarajaClient

logger = logging.getLogger(__name__)


class ClaimViewSet(viewsets.ModelViewSet):
    """ViewSet for insurance claims."""
    
    permission_classes = [IsAuthenticated]
    lookup_field = 'claim_id'
    ordering = ['-submitted_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer."""
        if self.action == 'create':
            return ClaimSubmitSerializer
        elif self.action in ['partial_update', 'update']:
            return ClaimReviewSerializer
        elif self.action == 'list':
            return ClaimListSerializer
        else:
            return ClaimDetailSerializer
    
    def get_queryset(self):
        """Return claims based on user role."""
        user = self.request.user
        
        if user.role == 'claims_officer':
            # Claims officer sees all submitted/pending claims
            return Claim.objects.filter(
                status__in=['submitted', 'under_review', 'info_requested']
            ).order_by('-submitted_at')
        
        elif user.role == 'super_admin':
            # Admin sees all claims
            return Claim.objects.all().order_by('-submitted_at')
        
        else:
            # Regular users see only their own claims
            return Claim.objects.filter(user_id=user).order_by('-submitted_at')
    
    def create(self, request, *args, **kwargs):
        """Submit new claim."""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        claim = serializer.save()
        
        # TODO: Trigger async GCP Document AI task for verification
        # For now, mark as under_review
        claim.status = 'under_review'
        claim.save()
        
        output_serializer = ClaimDetailSerializer(claim)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    def partial_update(self, request, *args, **kwargs):
        """Claims officer reviews claim."""
        # Only claims officers can review
        if request.user.role != 'claims_officer':
            return Response(
                {'error': 'Only claims officers can review claims'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        claim = self.get_object()
        serializer = ClaimReviewSerializer(
            claim,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # If approved, trigger payout
        if serializer.data['status'] == 'approved':
            self._trigger_payout(claim, request)
        
        output = ClaimDetailSerializer(claim)
        return Response(output.data)
    
    @action(detail=False, methods=['get'])
    def my_claims(self, request):
        """Get user's own claims."""
        claims = Claim.objects.filter(user_id=request.user).order_by('-submitted_at')
        serializer = ClaimListSerializer(claims, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending claims (claims officer view)."""
        if request.user.role != 'claims_officer':
            return Response(
                {'error': 'Only claims officers can view pending queue'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        claims = Claim.objects.filter(
            status__in=['submitted', 'under_review', 'info_requested']
        ).order_by('-submitted_at')
        serializer = ClaimListSerializer(claims, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def flagged(self, request):
        """Get AI-flagged claims (potential fraud)."""
        if request.user.role != 'claims_officer':
            return Response(
                {'error': 'Restricted access'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        claims = Claim.objects.filter(
            ai_flagged=True,
            status__in=['under_review', 'info_requested']
        ).order_by('-submitted_at')
        serializer = ClaimListSerializer(claims, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def approve_and_payout(self, request, claim_id=None):
        """Approve claim and initiate payout."""
        if request.user.role != 'claims_officer':
            return Response(
                {'error': 'Only claims officers can approve'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        claim = self.get_object()
        serializer = ClaimReviewSerializer(
            claim,
            data={'status': 'approved', 'decision_reason': request.data.get('reason')},
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Trigger B2C payout
        self._trigger_payout(claim, request)
        
        output = ClaimDetailSerializer(claim)
        return Response(output.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, claim_id=None):
        """Reject claim."""
        if request.user.role != 'claims_officer':
            return Response(
                {'error': 'Only claims officers can reject'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        claim = self.get_object()
        serializer = ClaimReviewSerializer(
            claim,
            data={
                'status': 'rejected',
                'decision_reason': request.data.get('reason', 'Claim rejected')
            },
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        output = ClaimDetailSerializer(claim)
        return Response(output.data)
    
    @action(detail=True, methods=['post'])
    def request_info(self, request, claim_id=None):
        """Request additional info from claimant."""
        if request.user.role != 'claims_officer':
            return Response({'error': 'Restricted'}, status=status.HTTP_403_FORBIDDEN)
        
        claim = self.get_object()
        serializer = ClaimReviewSerializer(
            claim,
            data={
                'status': 'info_requested',
                'decision_reason': request.data.get('reason', 'Additional info needed')
            },
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        output = ClaimDetailSerializer(claim)
        return Response(output.data)
    
    def _trigger_payout(self, claim, request):
        """Trigger B2C M-Pesa payout for approved claim."""
        try:
            user = claim.user_id
            phone = user.phone_number
            amount = int(claim.claim_amount)
            
            daraja = DarajaClient()
            response = daraja.b2c_payout(
                phone_number=phone,
                amount=amount,
                reference=str(claim.claim_id),
                description=f"Approved claim payout"
            )
            
            if response.get('ResponseCode') == '0':
                claim.status = 'paid'
                claim.payout_mpesa_ref = response.get('ConversationID')
                claim.paid_at = timezone.now()
                claim.save()
                
                logger.info(f"Payout initiated for claim {claim.claim_id}")
            else:
                logger.warning(f"Payout failed: {response.get('ResponseDescription')}")
        
        except Exception as e:
            logger.exception(f"Payout error for claim {claim.claim_id}")
