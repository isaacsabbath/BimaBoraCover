# For beginners: This file (apps/payments/urls.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

"""URLs for payments app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.payments.views import PaymentViewSet, mpesa_callback

router = DefaultRouter()
router.register(r'', PaymentViewSet, basename='payment')

urlpatterns = [
    path('callback/', mpesa_callback, name='mpesa-callback'),  # must come BEFORE router
    path('', include(router.urls)),
]