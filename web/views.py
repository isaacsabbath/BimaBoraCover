from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from apps.users.models import User
from apps.plans.models import InsurancePlan, Policy
from apps.claims.models import Claim
from apps.payments.models import Payment
from apps.payments.services.daraja import DarajaClient
from apps.chamas.models import Chama, ChamaMember


# ─── Auth ────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('web:home')
    if request.method == 'POST':
        user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
        if user:
            login(request, user)
            return redirect(request.POST.get('next') or 'web:home')
        from django.contrib.auth.forms import AuthenticationForm
        form = AuthenticationForm()
        form.errors['__all__'] = ['Invalid credentials']
        return render(request, 'web/login.html', {'form': form})
    return render(request, 'web/login.html', {})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('web:home')
    if request.method == 'POST':
        d = request.POST
        errors = []
        if d.get('password') != d.get('confirm_password'):
            errors.append('Passwords do not match.')
        if User.objects.filter(email=d.get('email')).exists():
            errors.append('Email already registered.')
        if User.objects.filter(phone_number=d.get('phone_number')).exists():
            errors.append('Phone number already registered.')
        if User.objects.filter(national_id=d.get('national_id')).exists():
            errors.append('National ID already registered.')
        if errors:
            return render(request, 'web/register.html', {'errors': errors, 'form_data': d})
        user = User.objects.create_user(
            email=d['email'],
            password=d['password'],
            full_name=d['full_name'],
            phone_number=d['phone_number'],
            national_id=d['national_id'],
            is_active=True,
        )
        login(request, user)
        messages.success(request, f'Welcome to BimaBora, {user.full_name}!')
        return redirect('web:home')
    return render(request, 'web/register.html', {})


def logout_view(request):
    logout(request)
    return redirect('web:login')


# ─── Home ─────────────────────────────────────────────────────────────────────

@login_required(login_url='web:login')
def home_view(request):
    active_policy = Policy.objects.filter(user_id=request.user, status='active').select_related('plan_id').first()
    recent_claims = Claim.objects.filter(user_id=request.user).order_by('-submitted_at')[:3]
    return render(request, 'web/home.html', {
        'active_policy': active_policy,
        'recent_claims': recent_claims,
    })


# ─── Explore ──────────────────────────────────────────────────────────────────

@login_required(login_url='web:login')
def explore_view(request):
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
    return render(request, 'web/explore.html', {'tabs': tabs})


@login_required(login_url='web:login')
@require_POST
def select_plan_view(request, plan_id):
    plan = get_object_or_404(InsurancePlan, plan_id=plan_id, status='active')
    messages.success(request, f'You selected {plan.plan_name}. Complete payment to activate.')
    return redirect('web:payment')


# ─── Claims ───────────────────────────────────────────────────────────────────

@login_required(login_url='web:login')
def claim_view(request):
    claims = Claim.objects.filter(user_id=request.user).order_by('-submitted_at')
    if request.method == 'POST':
        d = request.POST
        errors = []
        description = d.get('description', '')
        if len(description) < 50:
            errors.append('Description must be at least 50 characters.')
        if not d.get('claim_amount') or float(d.get('claim_amount', 0)) <= 0:
            errors.append('Enter a valid claim amount.')
        active_plan = InsurancePlan.objects.filter(status='active').first()
        if not active_plan:
            errors.append('No active insurance plan found.')
        if errors:
            return render(request, 'web/claim.html', {'errors': errors, 'claims': claims})
        Claim.objects.create(
            user_id=request.user,
            plan_id=active_plan,
            claim_type=d['claim_type'],
            claim_amount=d['claim_amount'],
            description=description,
            status='submitted',
        )
        messages.success(request, 'Claim submitted successfully. We will review it shortly.')
        return redirect('web:claim')
    return render(request, 'web/claim.html', {'claims': claims})


# ─── Payment ──────────────────────────────────────────────────────────────────

@login_required(login_url='web:login')
def payment_view(request):
    plans = InsurancePlan.objects.filter(status='active')
    active_policy = Policy.objects.filter(user_id=request.user, status='active').select_related('plan_id').first()
    payments = Payment.objects.filter(user_id=request.user).order_by('-initiated_at')[:10]

    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        d = request.POST
        plan_id = d.get('plan_id')
        amount = d.get('amount')
        phone = d.get('phone_number', '').strip()

        errors = []
        if not plan_id:
            errors.append('Select a plan.')
        if not amount or float(amount) < 10:
            errors.append('Minimum payment is KSh 10.')
        if not phone or len(phone) < 10:
            errors.append('Enter a valid phone number.')

        if errors:
            if is_ajax:
                return JsonResponse({'success': False, 'error': ' '.join(errors)})
            return render(request, 'web/payment.html', {'errors': errors, 'plans': plans, 'active_policy': active_policy, 'payments': payments})

        plan = get_object_or_404(InsurancePlan, plan_id=plan_id)

        # Format phone
        phone = phone.replace(' ', '').replace('-', '')
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif not phone.startswith('254'):
            phone = '254' + phone

        # Create payment record
        payment = Payment.objects.create(
            user_id=request.user,
            plan_id=plan,
            amount=amount,
            payment_type='premium',
            payment_direction='inbound',
            status='pending',
        )

        # Initiate Daraja STK Push
        try:
            daraja = DarajaClient()
            response = daraja.stk_push(
                phone_number=phone,
                amount=int(float(amount)),
                reference=str(payment.payment_id),
                description='Payment for insurance plan/premium'
            )
            if response.get('ResponseCode') == '0' and response.get('CheckoutRequestID'):
                payment.mpesa_ref = response.get('CheckoutRequestID', '')
                payment.save()
                if is_ajax:
                    return JsonResponse({'success': True, 'message': 'STK push sent. Check your phone to complete payment.'})
                messages.success(request, 'STK push sent. Check your phone.')
                return redirect('web:payment')
            else:
                payment.status = 'failed'
                payment.failure_reason = response.get('ResponseDescription', 'Unknown error')
                payment.save()
                if is_ajax:
                    return JsonResponse({'success': False, 'error': payment.failure_reason})
                messages.error(request, payment.failure_reason)
        except ValueError as e:
            payment.status = 'failed'
            payment.failure_reason = str(e)
            payment.save()
            if is_ajax:
                return JsonResponse({'success': False, 'error': str(e)})
            messages.error(request, str(e))
        except Exception as e:
            payment.status = 'failed'
            payment.failure_reason = str(e)
            payment.save()
            if is_ajax:
                return JsonResponse({'success': False, 'error': 'Payment service unavailable.'})
            messages.error(request, 'Payment service unavailable.')

    return render(request, 'web/payment.html', {
        'plans': plans,
        'active_policy': active_policy,
        'payments': payments,
    })


# ─── Chama ────────────────────────────────────────────────────────────────────

@login_required(login_url='web:login')
def chama_view(request):
    chama_ids = ChamaMember.objects.filter(user_id=request.user, status='active').values_list('chama_id', flat=True)
    chamas = Chama.objects.filter(chama_id__in=chama_ids).prefetch_related('members')
    return render(request, 'web/chama.html', {'chamas': chamas})


@login_required(login_url='web:login')
def chama_detail_view(request, chama_id):
    chama = get_object_or_404(Chama, chama_id=chama_id)
    members = ChamaMember.objects.filter(chama_id=chama, status='active').select_related('user_id')
    return render(request, 'web/chama_detail.html', {'chama': chama, 'members': members})


@login_required(login_url='web:login')
@require_POST
def chama_create_view(request):
    d = request.POST
    chama = Chama.objects.create(
        group_name=d['group_name'],
        registration_no=d['registration_no'],
        expected_members=int(d.get('expected_members', 2)),
        admin_id=request.user,
        status='active',
    )
    ChamaMember.objects.create(chama_id=chama, user_id=request.user, member_role='admin', status='active')
    messages.success(request, f'Chama "{chama.group_name}" created successfully!')
    return redirect('web:chama')


@login_required(login_url='web:login')
@require_POST
def chama_invite_view(request):
    chama_id = request.POST.get('chama_id')
    email = request.POST.get('email')
    chama = get_object_or_404(Chama, chama_id=chama_id, admin_id=request.user)
    try:
        invite_user = User.objects.get(email=email)
        ChamaMember.objects.get_or_create(chama_id=chama, user_id=invite_user, defaults={'status': 'active', 'member_role': 'member'})
        messages.success(request, f'{invite_user.full_name} added to {chama.group_name}.')
    except User.DoesNotExist:
        messages.error(request, 'User with that email not found.')
    return redirect('web:chama')


# ─── Profile ──────────────────────────────────────────────────────────────────

@login_required(login_url='web:login')
def profile_view(request):
    if request.method == 'POST':
        user = request.user
        user.full_name = request.POST.get('full_name', user.full_name)
        user.phone_number = request.POST.get('phone_number', user.phone_number)
        user.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('web:profile')
    return render(request, 'web/profile.html', {})


@login_required(login_url='web:login')
def change_password_view(request):
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
            return redirect('web:profile')
    return render(request, 'web/change_password.html', {})
