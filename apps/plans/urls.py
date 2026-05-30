"""URL routing for Insurance Plans and Policies."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InsurancePlanViewSet, PolicyViewSet

router = DefaultRouter()
router.register(r'plans', InsurancePlanViewSet, basename='insurance-plan')
router.register(r'policies', PolicyViewSet, basename='policy')

urlpatterns = [
    path('', include(router.urls)),
]
