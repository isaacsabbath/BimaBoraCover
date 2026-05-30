"""URLs for payments app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.payments.views import PaymentViewSet, mpesa_callback

router = DefaultRouter()
router.register(r'', PaymentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
    path('callback/', mpesa_callback, name='mpesa-callback'),
]
