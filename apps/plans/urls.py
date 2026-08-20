# For beginners: This file (apps/plans/urls.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

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
