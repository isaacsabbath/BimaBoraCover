# For beginners: This file (apps/claims/views.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

"""
Views for Insurance Claims workflow.
"""

from django.db import transaction
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
import logging

from apps.audit.models import AuditLog
from apps.claims.models import Claim, Notification
from apps.users.models import User
from apps.claims.serializers import (
    ClaimListSerializer, ClaimDetailSerializer,
    ClaimSubmitSerializer, ClaimReviewSerializer
)
from apps.payments.services.daraja import DarajaClient
from apps.claims.services.invoice_analyzer import InvoiceAnalyzerService
# from apps.users.services.azure_storage import AzureBlobStorageService  # Azure path kept for review
from apps.users.services.mongo_storage import MongoAtlasStorageService

logger = logging.getLogger(__name__)


# For beginners: This function '_claims_officer_guard' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
# For beginners: This function '_claims_officer_guard' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
def _claims_officer_guard(request):
    if not request.user.is_authenticated or request.user.role != 'claims_officer':
        messages.error(request, 'Only claims officers can access this page.')
        return redirect('home')
    return None


# For beginners: This function '_write_audit_entry' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
# For beginners: This function '_write_audit_entry' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
def _write_audit_entry(request, claim, event_type, metadata=None):
    AuditLog.objects.create(
        event_type=event_type,
        actor_id=request.user,
        target_model='Claim',
        target_id=claim.claim_id,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=(request.META.get('HTTP_USER_AGENT', '') or '')[:255],
        metadata=metadata or {},
    )


# For beginners: This function '_normalize_msisdn' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
# For beginners: This function '_normalize_msisdn' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
def _normalize_msisdn(phone_number):
    phone = str(phone_number or '').strip().replace(' ', '').replace('-', '')
    if phone.startswith('+'):
        phone = phone[1:]
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    elif phone and not phone.startswith('254'):
        phone = '254' + phone
    return phone


# For beginners: This function '_normalize_documents' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
# For beginners: This function '_normalize_documents' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
def _normalize_documents(documents):
    normalized = []
    for index, document in enumerate(documents or [], start=1):
        if isinstance(document, dict):
            url = document.get('url') or document.get('signed_url') or document.get('file_url')
            label = document.get('label') or document.get('name') or f'Document {index}'
        else:
            url = str(document)
            label = f'Document {index}'
        if url:
            normalized.append({'label': label, 'url': url})
    return normalized


# For beginners: This function '_store_uploaded_documents' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
# For beginners: This function '_store_uploaded_documents' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
def _store_uploaded_documents(user, files):
    stored_documents = []
    for uploaded_file in files:
        storage_path = default_storage.save(
            f'claims/{user.id}/{uploaded_file.name}',
            ContentFile(uploaded_file.read())
        )
        stored_documents.append({
            'label': uploaded_file.name,
            'url': default_storage.url(storage_path),
        })
    return stored_documents


# For beginners: This function '_ai_summary' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
# For beginners: This function '_ai_summary' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
def _ai_summary(ai_verification):
    if not ai_verification:
        return []

    if isinstance(ai_verification, dict):
        summary = []
        preferred_keys = [
            ('status', 'Status'),
            ('verdict', 'Verdict'),
            ('confidence', 'Confidence'),
            ('flag_reason', 'Flag Reason'),
            ('summary', 'Summary'),
            ('message', 'Message'),
        ]
        for key, label in preferred_keys:
            value = ai_verification.get(key)
            if value not in [None, '', [], {}]:
                summary.append({'label': label, 'value': value})
        if not summary:
            for key, value in ai_verification.items():
                summary.append({'label': key.replace('_', ' ').title(), 'value': value})
        return summary

    return [{'label': 'Result', 'value': ai_verification}]


# For beginners: This function 'await_ai_analysis' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
# For beginners: This function 'await_ai_analysis' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
def await_ai_analysis(claim, uploaded_files):
    """
    Process uploaded invoice documents with Azure AI Document Intelligence using custom models.
    
    Args:
        claim: Claim instance
        uploaded_files: List of uploaded file objects
    """
    if not uploaded_files:
        return
    
    try:
        # Initialize Mongo Atlas storage service for document upload.
        # blob_storage_service = AzureBlobStorageService()  # Azure path kept for review
        blob_storage_service = MongoAtlasStorageService()
        
        # Initialize Azure AI Document Intelligence service with custom model
        # Note: In production, you would specify your custom model name here
        invoice_analyzer = InvoiceAnalyzerService(model_name="your-custom-model-name")
        
        # Process each uploaded file
        ai_verification_results = []
        ai_flagged = False
        
        for uploaded_file in uploaded_files:
            try:
                # Upload file to Azure Blob Storage
                blob_url = blob_storage_service.upload_kyc_document(
                    file_obj=uploaded_file,
                    document_type="invoice",
                    user_id=claim.user_id.id,
                    filename=uploaded_file.name
                )
                
                # Analyze with Azure AI Document Intelligence using custom model
                # You can specify custom fields to extract here
                custom_fields = ["invoice_number", "total_amount", "vendor_name", "customer_name", "invoice_date"]
                result = invoice_analyzer.analyze_invoice(blob_url, custom_fields=custom_fields)
                
                if result['success']:
                    ai_verification_results.append(result['data'])
                    
                    # Check if any fields were flagged or confidence is low
                    if result['data'].get('confidence_score', 0) < 0.8:
                        ai_flagged = True
                        
                    # Check for specific invoice validation issues
                    invoice_data = result['data']
                    if invoice_data.get('total_amount') and float(invoice_data['total_amount']['value']) <= 0:
                        ai_flagged = True
                        
                    if invoice_data.get('vendor_name') and invoice_data['vendor_name'].get('confidence', 0) < 0.7:
                        ai_flagged = True
                else:
                    logger.warning(f"Failed to analyze invoice {uploaded_file.name}: {result['error']}")
                    
            except Exception as file_error:
                logger.error(f"Error processing file {uploaded_file.name}: {str(file_error)}")
                # Continue processing other files even if one fails
        
        # Store AI verification results
        if ai_verification_results:
            claim.ai_verification = ai_verification_results
            claim.ai_flagged = ai_flagged
            claim.save(update_fields=['ai_verification', 'ai_flagged'])
            
            logger.info(f"Processed {len(uploaded_files)} invoice documents for claim {claim.claim_id}")
            
    except Exception as e:
        logger.error(f"Error processing invoice documents for claim {claim.claim_id}: {str(e)}")
        # Don't fail the claim creation if AI analysis fails


# For beginners: This function '_attach_claim_context' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
# For beginners: This function '_attach_claim_context' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
def _attach_claim_context(claim):
    return {
        'claim': claim,
        'documents': _normalize_documents(claim.documents),
        'ai_summary': _ai_summary(claim.ai_verification),
    }


# For beginners: This function '_reject_or_request_info' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
# For beginners: This function '_reject_or_request_info' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
def _reject_or_request_info(request, claim, event_type, new_status, default_message, notification_prefix):
    reason = request.POST.get('reason', '').strip()
    if not reason:
        messages.error(request, 'Please provide a reason.')
        return redirect('claims_officer_detail', claim_id=claim.claim_id)

    with transaction.atomic():
        claim.status = new_status
        claim.reviewed_by = request.user
        claim.decision_reason = reason
        claim.decided_at = timezone.now()
        claim.save(update_fields=['status', 'reviewed_by', 'decision_reason', 'decided_at'])

        Notification.objects.create(
            recipient=claim.user_id,
            message=f"{notification_prefix}: {reason}",
        )

        _write_audit_entry(
            request,
            claim,
            event_type,
            {
                'reason': reason,
                'status': new_status,
            },
        )

    messages.success(request, default_message)
    return redirect('claims_officer_dashboard')


# For beginners: This function '_approve_claim' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
# For beginners: This function '_approve_claim' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
def _approve_claim(request, claim):
    claim.status = 'approved'
    claim.reviewed_by = request.user
    claim.decision_reason = claim.decision_reason or 'Approved by claims officer'
    claim.decided_at = timezone.now()
    claim.save(update_fields=['status', 'reviewed_by', 'decision_reason', 'decided_at'])

    payout_reference = ''
    payout_error = None

    try:
        daraja = DarajaClient()
        response = daraja.b2c_payout(
            phone_number=_normalize_msisdn(claim.user_id.phone_number),
            amount=claim.claim_amount,
            reference=str(claim.claim_id),
            description='Approved claim payout',
        )

        if str(response.get('ResponseCode', '')) != '0':
            raise ValueError(response.get('ResponseDescription', 'B2C payout failed'))

        payout_reference = (
            response.get('ConversationID')
            or response.get('OriginatorConversationID')
            or response.get('ResponseDescription', '')
        )

        claim.status = 'paid'
        claim.payout_mpesa_ref = payout_reference
        claim.paid_at = timezone.now()
        claim.save(update_fields=['status', 'payout_mpesa_ref', 'paid_at'])

    except Exception as exc:
        payout_error = str(exc)

    _write_audit_entry(
        request,
        claim,
        'claim_approved',
        {
            'status': claim.status,
            'payout_reference': payout_reference,
            'payout_error': payout_error,
        },
    )

    if payout_error:
        messages.error(
            request,
            f'Claim approved, but payout could not be completed: {payout_error}',
        )
    else:
        messages.success(request, 'Claim approved and paid successfully.')

    return redirect('claims_officer_dashboard')


# For beginners: This class 'ClaimViewSet' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'ClaimViewSet' groups related data and behavior
# so other parts of the app can use one structured object.
class ClaimViewSet(viewsets.ModelViewSet):
    """ViewSet for insurance claims."""
    
    permission_classes = [IsAuthenticated]
    lookup_field = 'claim_id'
    ordering = ['-submitted_at']
    
    # For beginners: This function 'get_serializer_class' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'get_serializer_class' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
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
    
    # For beginners: This function 'get_queryset' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'get_queryset' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
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
    
    # For beginners: This function 'create' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'create' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def create(self, request, *args, **kwargs):
        """Submit new claim."""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        claim = serializer.save()
        
        # Process uploaded documents with Azure AI Document Intelligence
        await_ai_analysis(claim, request.FILES.getlist('documents'))
        
        # TODO: Trigger async GCP Document AI task for verification
        # For now, mark as under_review
        claim.status = 'under_review'
        claim.save()

        _write_audit_entry(
            request,
            claim,
            'claim_submitted',
            {
                'claim_type': claim.claim_type,
                'claim_amount': str(claim.claim_amount),
                'status': claim.status,
            },
        )
        
        output_serializer = ClaimDetailSerializer(claim)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    # For beginners: This function 'partial_update' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'partial_update' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
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
    # For beginners: This function 'my_claims' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'my_claims' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def my_claims(self, request):
        """Get user's own claims."""
        claims = Claim.objects.filter(user_id=request.user).order_by('-submitted_at')
        serializer = ClaimListSerializer(claims, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    # For beginners: This function 'pending' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'pending' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
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
    # For beginners: This function 'flagged' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'flagged' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
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
    # For beginners: This function 'approve_and_payout' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'approve_and_payout' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
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
    # For beginners: This function 'reject' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'reject' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
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
    # For beginners: This function 'request_info' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'request_info' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
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
    
    # For beginners: This function '_trigger_payout' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function '_trigger_payout' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def _trigger_payout(self, claim, request):
        """Trigger B2C M-Pesa payout for approved claim."""
        try:
            user = claim.user_id
            phone = user.phone_number
            amount = int(claim.claim_amount)
            daraja = DarajaClient()
            response = daraja.b2c_payout(
                phone_number=phone, amount=amount,
                reference=str(claim.claim_id), description=f"Approved claim payout"
            )
            if response.get('ResponseCode') == '0':
                claim.status = 'paid'
                claim.payout_mpesa_ref = response.get('ConversationID')
                claim.paid_at = timezone.now()
                claim.save()
        except Exception as e:
            logger.exception(f"Payout error for claim {claim.claim_id}")


# ─── Template Views ───────────────────────────────────────────────────────────


@login_required(login_url='login')
# For beginners: This function 'claims_officer_dashboard_page' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
# For beginners: This function 'claims_officer_dashboard_page' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
def claims_officer_dashboard_page(request):
    guard = _claims_officer_guard(request)
    if guard:
        return guard

    claims = Claim.objects.filter(
        status__in=['submitted', 'under_review']
    ).select_related('user_id').order_by('-ai_flagged', '-submitted_at')
    kyc_queue_count = User.objects.filter(kyc_status='review').count()

    return render(request, 'claims/officer_dashboard.html', {
        'claims': claims,
        'kyc_queue_count': kyc_queue_count,
    })


@login_required(login_url='login')
# For beginners: This function 'claim_detail_page' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
# For beginners: This function 'claim_detail_page' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
def claim_detail_page(request, claim_id):
    guard = _claims_officer_guard(request)
    if guard:
        return guard

    claim = get_object_or_404(
        Claim.objects.select_related('user_id', 'reviewed_by', 'plan_id'),
        claim_id=claim_id,
    )

    if request.method == 'POST':
        if claim.status not in ['submitted', 'under_review']:
            messages.error(request, 'This claim has already been reviewed.')
            return redirect('claims_officer_dashboard')

        action = request.POST.get('action')

        if action == 'approve':
            return _approve_claim(request, claim)

        if action == 'reject':
            return _reject_or_request_info(
                request,
                claim,
                'claim_rejected',
                'rejected',
                'Claim rejected successfully.',
                'Your claim was rejected',
            )

        if action == 'request_info':
            return _reject_or_request_info(
                request,
                claim,
                'claim_info_requested',
                'info_requested',
                'More information requested successfully.',
                'More information is required for your claim',
            )

        messages.error(request, 'Unsupported action.')

    return render(request, 'claims/officer_detail.html', _attach_claim_context(claim))

@login_required(login_url='login')
# For beginners: This function 'claim_page' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
# For beginners: This function 'claim_page' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
def claim_page(request):
    from apps.plans.models import InsurancePlan
    claims = Claim.objects.filter(user_id=request.user).order_by('-submitted_at')
    if request.method == 'POST':
        d = request.POST
        errors = []
        if len(d.get('description', '')) < 50:
            errors.append('Description must be at least 50 characters.')
        if not d.get('claim_amount') or float(d.get('claim_amount', 0)) <= 0:
            errors.append('Enter a valid claim amount.')
        plan = InsurancePlan.objects.filter(status='active').first()
        if not plan:
            errors.append('No active insurance plan found in the system.')
        if errors:
            return render(request, 'claims/form.html', {'errors': errors, 'claims': claims})
        documents = _store_uploaded_documents(request.user, request.FILES.getlist('documents'))
        claim = Claim.objects.create(
            user_id=request.user, plan_id=plan,
            claim_type=d['claim_type'], claim_amount=d['claim_amount'],
            description=d['description'], status='submitted',
            documents=documents,
        )
        _write_audit_entry(
            request,
            claim,
            'claim_submitted',
            {
                'claim_type': claim.claim_type,
                'claim_amount': str(claim.claim_amount),
                'document_count': len(documents),
            },
        )
        messages.success(request, 'Claim submitted successfully.')
        return redirect('claim')
    return render(request, 'claims/form.html', {'claims': claims})
