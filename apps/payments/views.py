# For beginners: This file (apps/payments/views.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

"""
Views for M-Pesa payment processing.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from decimal import Decimal
from django.db import transaction
from apps.plans.models import Policy
import datetime
import json
import logging

from apps.payments.models import Payment
from apps.payments.serializers import (
    PaymentInitiateSerializer, PaymentListSerializer,
    PaymentDetailSerializer
)
from apps.payments.services.daraja import DarajaClient

logger = logging.getLogger(__name__)


# For beginners: This class 'PaymentViewSet' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'PaymentViewSet' groups related data and behavior
# so other parts of the app can use one structured object.
class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet for payment processing."""
    
    permission_classes = [IsAuthenticated]
    lookup_field = 'payment_id'
    ordering = ['-initiated_at']
    
    # For beginners: This function 'get_serializer_class' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'get_serializer_class' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def get_serializer_class(self):
        """Return appropriate serializer."""
        if self.action == 'initiate':
            return PaymentInitiateSerializer
        elif self.action == 'list':
            return PaymentListSerializer
        else:
            return PaymentDetailSerializer
    
    # For beginners: This function 'get_queryset' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'get_queryset' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def get_queryset(self):
        """Return user's payments."""
        return Payment.objects.filter(user_id=self.request.user).order_by('-initiated_at')
    
    @action(detail=False, methods=['post'])
    # For beginners: This function 'initiate' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'initiate' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def initiate(self, request):
        """Initiate STK push payment request."""
        serializer = PaymentInitiateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            daraja = DarajaClient()
            
            # Create payment record
            payment = Payment.objects.create(
                user_id=request.user,
                amount=serializer.validated_data['amount'],
                payment_direction='inbound',
                payment_type='premium',
                plan_id_id=serializer.validated_data.get('plan_id'),
                status='pending'
            )
            
            # Initiate STK push
            response = daraja.stk_push(
                phone_number=serializer.validated_data['phone_number'],
                amount=int(serializer.validated_data['amount']),
                reference=str(payment.payment_id),
                description=f"Payment for insurance plan/premium"
            )
            
            if response.get('ResponseCode') != '0':
                payment.status = 'failed'
                payment.failure_reason = response.get('ResponseDescription', 'STK push failed')
                payment.save()
                
                return Response({
                    'error': payment.failure_reason,
                    'response_code': response.get('ResponseCode')
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Store checkout request ID for poll
            payment.metadata = {
                'checkout_request_id': response.get('CheckoutRequestID'),
                'phone_number': serializer.validated_data['phone_number']
            }
            payment.save()
            
            return Response({
                'payment_id': str(payment.payment_id),
                'status': 'pending',
                'amount': str(payment.amount),
                'checkout_request_id': response.get('CheckoutRequestID'),
                'message': 'Check your phone for STK prompt',
                'timeout_seconds': 180
            }, status=status.HTTP_201_CREATED)
        
        except ValueError as e:
            payment.status = 'failed'
            payment.failure_reason = str(e)
            payment.save()
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            logger.exception("STK push error")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    # For beginners: This function 'status' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'status' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def status(self, request, payment_id=None):
        """Poll payment status."""
        payment = self.get_object()
        
        # If already confirmed or failed, return current status
        if payment.status in ['confirmed', 'failed']:
            serializer = PaymentDetailSerializer(payment)
            return Response(serializer.data)
        
        # Query Daraja for status
        try:
            checkout_id = payment.metadata.get('checkout_request_id')
            if not checkout_id:
                return Response({
                    'status': payment.status,
                    'message': 'Payment status unknown'
                })
            
            daraja = DarajaClient()
            response = daraja.check_transaction_status(checkout_id)
            
            # Update payment if completed
            if response.get('ResultCode') == '0':
                payment.status = 'confirmed'
                payment.mpesa_ref = response.get('MerchantRequestID')
                payment.confirmed_at = timezone.now()
                payment.save()
            
            serializer = PaymentDetailSerializer(payment)
            return Response(serializer.data)
        
        except Exception as e:
            logger.exception("Status check error")
            return Response({
                'error': 'Could not check status',
                'status': payment.status
            })
    
    @action(detail=False, methods=['get'])
    # For beginners: This function 'history' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'history' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def history(self, request):
        """Get payment history."""
        payments = self.get_queryset()
        serializer = PaymentListSerializer(payments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    # For beginners: This function 'pending' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'pending' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def pending(self, request):
        """Get pending payments."""
        payments = self.get_queryset().filter(status='pending')
        serializer = PaymentListSerializer(payments, many=True)
        return Response(serializer.data)


# M-Pesa callback endpoint (no auth required)
@require_http_methods(["POST"])
@csrf_exempt
# For beginners: This function 'mpesa_callback' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
# For beginners: This function 'mpesa_callback' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
def mpesa_callback(request):
    try:
        data = json.loads(request.body)
        logger.info(f"M-Pesa callback received: {data}")

        body = data.get('Body', {})
        stk_callback = body.get('stkCallback', {})

        result_code = stk_callback.get('ResultCode')
        result_desc = stk_callback.get('ResultDesc')
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        merchant_request_id = stk_callback.get('MerchantRequestID')

        try:
            payment = Payment.objects.get(
                metadata__checkout_request_id=checkout_request_id
            )

            if result_code == 0:
                # Extract M-Pesa receipt
                mpesa_receipt = merchant_request_id
                callback_metadata = stk_callback.get('CallbackMetadata', {})
                items = callback_metadata.get('Item', [])
                for item in items:
                    if item.get('Name') == 'MpesaReceiptNumber':
                        mpesa_receipt = item.get('Value')

                # Atomic transaction — payment + policy activation together
                with transaction.atomic():
                    # 1. Confirm payment
                    payment.status = 'confirmed'
                    payment.mpesa_ref = mpesa_receipt
                    payment.confirmed_at = timezone.now()
                    payment.save()

                    # 2. Activate the plan if payment has a plan
                    if payment.plan_id:
                        # Deactivate any existing active policy
                        Policy.objects.filter(
                            user_id=payment.user_id,
                            status='active'
                        ).update(status='expired')

                        # Activate new policy
                        policy, created = Policy.objects.get_or_create(
                            user_id=payment.user_id,
                            plan_id=payment.plan_id,
                            defaults={
                                'status': 'active',
                                'end_date': timezone.now() + datetime.timedelta(days=365),
                                'premium_paid': payment.amount,
                                # TODO: confirm this is the right source for coverage_amount
                                'coverage_amount': payment.plan_id.max_coverage,
                                'payment_reference': mpesa_receipt,
                            }
                        )

                        if not created:
                            # Policy exists, reactivate it
                            policy.status = 'active'
                            policy.end_date = timezone.now() + datetime.timedelta(days=365)
                            policy.premium_paid = payment.amount
                            policy.payment_reference = mpesa_receipt
                            policy.save()

                        logger.info(
                            f"Policy activated for user "
                            f"{payment.user_id} — plan {payment.plan_id}"
                        )

                logger.info(f"Payment {payment.payment_id} confirmed")

            else:
                # Payment failed — just update status
                with transaction.atomic():
                    payment.status = 'failed'
                    payment.failure_reason = result_desc
                    payment.save()

                logger.info(f"Payment {payment.payment_id} failed: {result_desc}")

        except Payment.DoesNotExist:
            logger.warning(
                f"Payment not found for checkout_id: {checkout_request_id}"
            )

        return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Accepted'})

    except Exception as e:
        logger.exception("Callback processing error")
        return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Error'}, status=400)

    except Exception as e:
        logger.exception("Callback processing error")
        return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Error'}, status=400)


# ─── Template Views ───────────────────────────────────────────────────────────
@login_required(login_url='login')
# For beginners: This function 'payment_page' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
# For beginners: This function 'payment_page' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
def payment_page(request):
    from apps.plans.models import InsurancePlan, Policy
    from django.db import transaction

    plans = InsurancePlan.objects.filter(status='active')
    active_policy = Policy.objects.filter(
        user_id=request.user, status='active'
    ).select_related('plan_id').first()
    payments = Payment.objects.filter(
        user_id=request.user
    ).order_by('-initiated_at')[:10]

    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        d = request.POST
        plan_id = d.get('plan_id')
        amount = d.get('amount', '0')
        phone = d.get('phone_number', '').strip().replace(' ', '').replace('-', '')

        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif not phone.startswith('254'):
            phone = '254' + phone

        plan = get_object_or_404(InsurancePlan, plan_id=plan_id) if plan_id else None

        try:
            with transaction.atomic():
                payment = Payment.objects.create(
                    user_id=request.user,
                    plan_id=plan,
                    amount=amount,
                    payment_type='premium',
                    payment_direction='inbound',
                    status='pending',
                )

                daraja = DarajaClient()
                response = daraja.stk_push(
                    phone_number=phone,
                    amount=int(float(amount)),
                    reference=str(payment.payment_id),
                    description='Payment for insurance plan/premium'
                )

                if response.get('ResponseCode') == '0' and response.get('CheckoutRequestID'):
                    payment.metadata = {
                        'checkout_request_id': response.get('CheckoutRequestID'),
                        'phone_number': phone
                    }
                    payment.save()

                    if is_ajax:
                        return JsonResponse({
                            'success': True,
                            'message': 'STK push sent. Check your phone.',
                            'payment_id': str(payment.payment_id)
                        })

                    messages.success(request, 'STK push sent. Check your phone.')
                    return redirect('payment')

                else:
                    payment.status = 'failed'
                    payment.failure_reason = response.get(
                        'ResponseDescription', 'Unknown error'
                    )
                    payment.save()
                    raise ValueError(payment.failure_reason)

        except ValueError as e:
            if is_ajax:
                return JsonResponse({'success': False, 'error': str(e)})
            messages.error(request, str(e))
            return render(request, 'payments/dashboard.html', {
                'plans': plans,
                'active_policy': active_policy,
                'payments': payments,
            })

        except Exception as e:
            logger.exception("STK push error")
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'error': 'Payment service unavailable.'
                })
            messages.error(request, 'Payment service unavailable.')
            return render(request, 'payments/dashboard.html', {
                'plans': plans,
                'active_policy': active_policy,
                'payments': payments,
            })

    # GET request
    return render(request, 'payments/dashboard.html', {
        'plans': plans,
        'active_policy': active_policy,
        'payments': payments,
    })