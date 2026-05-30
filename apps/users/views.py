"""
API views + Template views for users app.
"""

import mimetypes
import secrets
import string
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.urls import reverse
from django.views.decorators.http import require_POST
from django_q.tasks import async_task
from django.db import transaction
from django.db.utils import OperationalError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView as JWTTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView
from .models import User
from .serializers import (
    UserSerializer, UserDetailSerializer, RegisterSerializer,
    OTPVerifySerializer, TokenObtainPairSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    ProfileUpdateSerializer
)


def _generate_temp_password(length=10):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def _generate_setup_code(length=6):
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def _generate_autogen_email(national_id):
    """Create a unique internal email when signup is driven by doc extraction."""
    base = f"{str(national_id).strip().lower()}@autogen.bimabora.local"
    if base and not User.objects.filter(email=base).exists():
        return base

    # Ensure uniqueness if the base has already been used.
    for _ in range(10):
        candidate = f"{str(national_id).strip().lower()}-{secrets.token_hex(2)}@autogen.bimabora.local"
        if not User.objects.filter(email=candidate).exists():
            return candidate

    return f"user-{secrets.token_hex(4)}@autogen.bimabora.local"


def _is_claims_officer_setup_pending(user):
    return user.role == 'claims_officer' and bool(user.otp_code)


class RegisterView(viewsets.ViewSet):
    """User registration endpoint."""
    
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        """
        Register a new user account.
        
        Body:
            {
                "full_name": "John Doe",
                "national_id": "12345678",
                "phone_number": "+254712345678",
                "email": "user@example.com",
                "password": "securepassword123",
                "confirm_password": "securepassword123",
                "role": "individual"
            }
        """
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    'message': 'Account created successfully. OTP sent to your phone.',
                    'user': UserSerializer(user).data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OTPVerifyView(viewsets.ViewSet):
    """OTP verification endpoint."""
    
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def verify(self, request):
        """
        Verify OTP and activate account.
        
        Body:
            {
                "email": "user@example.com",
                "otp_code": "123456"
            }
        """
        serializer = OTPVerifySerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    'message': 'OTP verified successfully. Account activated.',
                    'user': UserSerializer(user).data
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TokenObtainPairView(JWTTokenObtainPairView):
    """Custom JWT token endpoint with role and kyc_status."""
    
    serializer_class = TokenObtainPairSerializer


class MeView(viewsets.ViewSet):
    """Get and update authenticated user profile."""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get authenticated user's profile."""
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch'])
    def update_profile(self, request):
        """Update authenticated user's profile."""
        serializer = ProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    'message': 'Profile updated successfully.',
                    'user': UserDetailSerializer(request.user).data
                }
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─── Template Views ───────────────────────────────────────────────────────────

def login_page(request):
    if request.user.is_authenticated:
        if _is_claims_officer_setup_pending(request.user):
            return redirect('claims_officer_setup_password')
        return redirect('home')
    if request.method == 'POST':
        user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
        if user:
            login(request, user)
            if _is_claims_officer_setup_pending(user):
                return redirect('claims_officer_setup_password')
            return redirect(request.POST.get('next') or 'home')
        return render(request, 'users/login.html', {'error': True})
    return render(request, 'users/login.html', {})


def register_page(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        d = request.POST.copy()
        phone = d.get('phone_number', '').strip().replace(' ', '').replace('-', '')
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif not phone.startswith('254') and phone:
            phone = '254' + phone
        if phone and not phone.startswith('+'):
            phone = '+' + phone
        d['phone_number'] = phone

        email_value = (d.get('email') or '').strip().lower()
        if not email_value and d.get('national_id'):
            email_value = _generate_autogen_email(d.get('national_id'))
            d['email'] = email_value

        serializer = RegisterSerializer(data={
            'full_name': d['full_name'],
            'national_id': d['national_id'],
            'phone_number': d['phone_number'],
            'email': email_value,
            'password': d['password'],
            'confirm_password': d['confirm_password'],
            'role': d.get('role', 'individual'),
        })
        if serializer.is_valid():
            user_data = serializer.validated_data
            user = User.objects.create_user(
                email=user_data['email'],
                password=user_data['password'],
                full_name=user_data['full_name'],
                phone_number=user_data['phone_number'],
                national_id=user_data['national_id'],
                role=user_data.get('role', 'individual'),
                is_active=True,
            )
            login(request, user)
            messages.success(request, f'Welcome to BimaBora, {user.full_name}!')
            return redirect('home')

        errors = []
        for field_errors in serializer.errors.values():
            if isinstance(field_errors, list):
                errors.extend(field_errors)
            else:
                errors.append(str(field_errors))
        return render(request, 'users/register.html', {'errors': errors, 'form_data': d})
    return render(request, 'users/register.html', {})



def logout_page(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def profile_page(request):
    if request.method == 'POST':
        u = request.user
        u.full_name = request.POST.get('full_name', u.full_name)
        u.phone_number = request.POST.get('phone_number', u.phone_number)
        u.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')
    return render(request, 'users/profile.html', {})


@login_required(login_url='login')
def change_password_page(request):
    if request.method == 'POST':
        old = request.POST.get('old_password')
        new = request.POST.get('new_password')
        confirm = request.POST.get('confirm_password')
        if not request.user.check_password(old):
            messages.error(request, 'Current password is incorrect.')
        elif new != confirm:
            messages.error(request, 'New passwords do not match.')
        elif len(new) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        else:
            request.user.set_password(new)
            request.user.save()
            login(request, request.user)
            messages.success(request, 'Password changed successfully.')
            return redirect('profile')
    return render(request, 'users/change_password.html', {})


def otp_verify_page(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        serializer = OTPVerifySerializer(data={
            'email': request.POST.get('email', '').strip(),
            'otp_code': request.POST.get('otp_code', '').strip(),
        })
        if serializer.is_valid():
            user = serializer.save()
            login(request, user)
            messages.success(request, 'Account verified. Welcome to BimaBora!')
            return redirect('home')
        return render(request, 'users/otp_verify.html', {
            'errors': serializer.errors,
            'email': request.POST.get('email', '').strip(),
        })

    return render(request, 'users/otp_verify.html', {
        'email': request.GET.get('email', ''),
    })


def password_reset_request_page(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        user = User.objects.filter(email=email).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = request.build_absolute_uri(
                reverse('password_reset_confirm', args=[uid, token])
            )
            send_mail(
                subject='BimaBora password reset',
                message=f'Use this link to reset your password: {reset_link}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        messages.success(request, 'If the email exists, a reset link has been sent.')
        return redirect('login')
    return render(request, 'users/password_reset_request.html', {})


@login_required(login_url='login')
def claims_officer_queue_page(request):
    """Simple claims officer triage page for KYC `review` items.

    GET: show list of users with `kyc_status='review'`.
    POST: take action for a user: `verify`, `flag`, or `reject` (via `action` and `user_id`).
    Only accessible to users with role `claims_officer` or staff.
    """
    # Authorization
    if not (request.user.is_staff or request.user.role == User.RoleChoices.CLAIMS_OFFICER):
        return redirect('home')

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')

        target = User.objects.filter(id=user_id).first()
        if target:
            if action == 'verify':
                target.kyc_status = 'verified'
                target.kyc_verified_at = timezone.now()
                # reflect decision in stored result
                if target.kyc_verification_result:
                    try:
                        target.kyc_verification_result.setdefault('authenticity', {})['decision'] = 'verified'
                    except Exception:
                        pass
                target.save()
                messages.success(request, f"Marked {target.email} as verified.")
            elif action == 'flag':
                target.kyc_status = 'flagged'
                if target.kyc_verification_result:
                    try:
                        target.kyc_verification_result.setdefault('authenticity', {})['decision'] = 'flagged'
                    except Exception:
                        pass
                target.save()
                messages.success(request, f"Marked {target.email} as flagged.")
            elif action == 'reject':
                target.kyc_status = 'rejected'
                if target.kyc_verification_result:
                    try:
                        target.kyc_verification_result.setdefault('authenticity', {})['decision'] = 'rejected'
                    except Exception:
                        pass
                target.save()
                messages.success(request, f"Marked {target.email} as rejected.")
        return redirect('claims_officer_queue')

    # GET: list users needing review
    review_qs = User.objects.filter(kyc_status='review').order_by('-kyc_verified_at', '-created_at')[:200]
    return render(request, 'users/claims_officer_queue.html', {'queue': review_qs})


def password_reset_confirm_page(request, uidb64, token):
    user = None
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=user_id)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        user = None

    if not user or not default_token_generator.check_token(user, token):
        messages.error(request, 'Invalid or expired password reset link.')
        return redirect('password_reset_request')

    if request.method == 'POST':
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        if new_password != confirm_password:
            return render(request, 'users/password_reset_confirm.html', {
                'error': 'Passwords do not match.',
            })
        if len(new_password) < 8:
            return render(request, 'users/password_reset_confirm.html', {
                'error': 'Password must be at least 8 characters.',
            })
        user.set_password(new_password)
        user.save()
        messages.success(request, 'Password reset successful. Please login.')
        return redirect('login')

    return render(request, 'users/password_reset_confirm.html', {})


@login_required(login_url='login')
def dashboard_page(request):
    if request.user.role == 'claims_officer':
        return redirect('claims_officer_dashboard')
    if request.user.role == 'super_admin':
        return render(request, 'users/dashboard.html', {
            'active_policy': None,
            'recent_claims': [],
            'notifications': [],
            'super_admin_mode': True,
        })

    from apps.plans.models import Policy
    from apps.claims.models import Claim
    from apps.claims.models import Notification

    active_policy = Policy.objects.filter(user_id=request.user, status='active').select_related('plan_id').first()
    recent_claims = Claim.objects.filter(user_id=request.user).order_by('-submitted_at')[:3]
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:8]
    return render(request, 'users/dashboard.html', {
        'active_policy': active_policy,
        'recent_claims': recent_claims,
        'notifications': notifications,
    })


@login_required(login_url='login')
def claims_officer_setup_password_page(request):
    if request.user.role != 'claims_officer' or not request.user.otp_code:
        return redirect('claims_officer_dashboard')

    if request.method == 'POST':
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        elif new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
        else:
            request.user.set_password(new_password)
            request.user.otp_code = ''
            request.user.otp_created_at = None
            request.user.save(update_fields=['password', 'otp_code', 'otp_created_at'])
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Password set successfully. Welcome to the dashboard.')
            return redirect('claims_officer_dashboard')

    return render(request, 'users/claims_officer_setup_password.html', {})


@login_required(login_url='login')
def create_claims_officer_page(request):
    if request.user.role != 'super_admin':
        messages.error(request, 'Only super admins can create claims officers.')
        return redirect('home')

    created_account = request.session.pop('claims_officer_created', None)

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        national_id = request.POST.get('national_id', '').strip()
        phone_number = request.POST.get('phone_number', '').strip().replace(' ', '').replace('-', '')

        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        elif phone_number and not phone_number.startswith('254'):
            phone_number = '254' + phone_number
        if phone_number and not phone_number.startswith('+'):
            phone_number = '+' + phone_number

        errors = []
        if not full_name:
            errors.append('Full name is required.')
        if not email:
            errors.append('Email is required.')
        if not national_id:
            errors.append('National ID is required.')
        if not phone_number:
            errors.append('Phone number is required.')

        if User.objects.filter(email=email).exists():
            errors.append('Email is already registered.')
        if User.objects.filter(national_id=national_id).exists():
            errors.append('National ID is already registered.')
        if User.objects.filter(phone_number=phone_number).exists():
            errors.append('Phone number is already registered.')

        if errors:
            return render(request, 'users/create_claims_officer.html', {
                'errors': errors,
                'form_data': request.POST,
            })

        setup_password = _generate_temp_password()
        setup_code = _generate_setup_code()

        with transaction.atomic():
            created_account = User.objects.create_user(
                email=email,
                password=setup_password,
                full_name=full_name,
                national_id=national_id,
                phone_number=phone_number,
                role='claims_officer',
                is_active=True,
            )
            created_account.otp_code = setup_code
            created_account.otp_created_at = timezone.now()
            created_account.save(update_fields=['otp_code', 'otp_created_at'])

        try:
            reset_link = request.build_absolute_uri(reverse('claims_officer_setup_password'))
            send_mail(
                subject='Claims Officer account ready',
                message=(
                    f'Your BimaBora claims officer account is ready.\n\n'
                    f'Login email: {email}\n'
                    f'Temporary password: {setup_password}\n\n'
                    f'After logging in, you will be prompted to set your own password at: {reset_link}'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )
        except Exception:
            pass

        messages.success(request, 'Claims Officer account created.')
        request.session['claims_officer_created'] = {
            'email': created_account.email,
            'setup_password': setup_password,
        }
        return redirect('create_claims_officer')

    return render(request, 'users/create_claims_officer.html', {
        'created_account': created_account,
        'setup_password': created_account['setup_password'] if created_account else None,
    })


class PasswordResetView(viewsets.ViewSet):
    """Password reset endpoints."""
    
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def request_reset(self, request):
        """Request password reset token via email."""
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            # TODO: Generate reset token and send email
            return Response({
                'message': 'Password reset link sent to your email.'
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def confirm_reset(self, request):
        """Confirm password reset with token."""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            # TODO: Validate token and update password
            return Response({
                'message': 'Password updated successfully.'
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
