# For beginners: This file (apps/claims/urls.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

"""URLs for claims app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.claims.views import ClaimViewSet

router = DefaultRouter()
router.register(r'', ClaimViewSet, basename='claim')

urlpatterns = [
    path('', include(router.urls)),
]
