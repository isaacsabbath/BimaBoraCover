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