# For beginners: This file (apps/users/urls.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

"""
URL patterns for users app.
"""

from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, OTPVerifyView, TokenObtainPairView,
    MeView, PasswordResetView, KYCView
)

router = DefaultRouter()
router.register(r'register', RegisterView, basename='register')
router.register(r'otp', OTPVerifyView, basename='otp')
router.register(r'me', MeView, basename='me')
router.register(r'password-reset', PasswordResetView, basename='password-reset')
router.register(r'kyc', KYCView, basename='kyc')

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
] + router.urls
