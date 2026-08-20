# For beginners: This file (apps/chamas/urls.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

"""URL routing for Chama endpoints."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChamaViewSet

router = DefaultRouter()
router.register(r'chamas', ChamaViewSet, basename='chama')

urlpatterns = [
    path('', include(router.urls)),
]
