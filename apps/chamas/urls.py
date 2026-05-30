"""URL routing for Chama endpoints."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChamaViewSet

router = DefaultRouter()
router.register(r'chamas', ChamaViewSet, basename='chama')

urlpatterns = [
    path('', include(router.urls)),
]
