# For beginners: This file (config/urls.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.users.views import (
    login_page,
    register_page,
    logout_page,
    profile_page,
    change_password_page,
    otp_verify_page,
    password_reset_request_page,
    password_reset_confirm_page,
    claims_officer_setup_password_page,
    create_claims_officer_page,
    dashboard_page,
    claims_officer_queue_page,
)
from apps.plans.views import explore_page, select_plan_page, plan_detail_page
from apps.claims.views import claim_page
from apps.claims.views import claims_officer_dashboard_page, claim_detail_page
from apps.claims.views import claims_officer_payouts_page, claims_officer_retry_payout
from apps.payments.views import payment_page
from apps.chamas.views import chama_page, chama_detail_page, chama_create_page, chama_invite_page, chama_invite_accept_page
from apps.users.views import sms_delivery_callback


urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # Template Pages
    path('', dashboard_page, name='home'),
    path('login/', login_page, name='login'),
    path('register/', register_page, name='register'),
    path('otp/verify/', otp_verify_page, name='otp_verify'),
    path('password-reset/', password_reset_request_page, name='password_reset_request'),
    path('password-reset/<uidb64>/<token>/', password_reset_confirm_page, name='password_reset_confirm'),
    path('logout/', logout_page, name='logout'),
    path('profile/', profile_page, name='profile'),
    path('profile/change-password/', change_password_page, name='change_password'),
    path('claims-officer/setup-password/', claims_officer_setup_password_page, name='claims_officer_setup_password'),
    path('super-admin/claims-officers/create/', create_claims_officer_page, name='create_claims_officer'),
    path('explore/', explore_page, name='explore'),
    path('explore/<uuid:plan_id>/', plan_detail_page, name='plan_detail'),
    path('explore/select/<uuid:plan_id>/', select_plan_page, name='select_plan'),
    path('claim/', claim_page, name='claim'),
    path('claims/officer/', claims_officer_dashboard_page, name='claims_officer_dashboard'),
    path('claims/officer/payouts/', claims_officer_payouts_page, name='claims_officer_payouts'),
    path('claims/officer/payouts/<uuid:claim_id>/retry/', claims_officer_retry_payout, name='claims_officer_retry_payout'),
    path('claims/officer/<uuid:claim_id>/', claim_detail_page, name='claims_officer_detail'),
    path('claims-officer/queue/', claims_officer_queue_page, name='claims_officer_queue'),
    path('payment/', payment_page, name='payment'),
    path('chama/', chama_page, name='chama'),
    path('chama/create/', chama_create_page, name='chama_create'),
    path('chama/invite/', chama_invite_page, name='chama_invite'),
    path('chama/invite/accept/<str:token>/', chama_invite_accept_page, name='chama_invite_accept'),
    path('chama/<uuid:chama_id>/', chama_detail_page, name='chama_detail'),

    # REST API
    path('api/v1/', include([
        path('auth/', include('apps.users.urls')),
        path('chamas/', include('apps.chamas.urls')),
        path('plans/', include('apps.plans.urls')),
        path('payments/', include('apps.payments.urls')),
        path('claims/', include('apps.claims.urls')),
        path('admin/', include('apps.audit.urls')),
        path('sms/delivery-callback/', sms_delivery_callback, name='sms-delivery-callback'),
    ])),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
