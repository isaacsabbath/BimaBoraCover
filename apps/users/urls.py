"""
URL patterns for users app.
"""

from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, OTPVerifyView, TokenObtainPairView,
    MeView, PasswordResetView
)

router = DefaultRouter()
router.register(r'register', RegisterView, basename='register')
router.register(r'otp', OTPVerifyView, basename='otp')
router.register(r'me', MeView, basename='me')
router.register(r'password-reset', PasswordResetView, basename='password-reset')

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
] + router.urls
