"""URLs for claims app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.claims.views import ClaimViewSet

router = DefaultRouter()
router.register(r'', ClaimViewSet, basename='claim')

urlpatterns = [
    path('', include(router.urls)),
]
