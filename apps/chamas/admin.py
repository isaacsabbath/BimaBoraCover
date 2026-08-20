# For beginners: This file (apps/chamas/admin.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

"""
Django admin configuration for chamas app.
"""

from django.contrib import admin
from .models import Chama, ChamaMember


@admin.register(Chama)
# For beginners: This class 'ChamaAdmin' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'ChamaAdmin' groups related data and behavior
# so other parts of the app can use one structured object.
class ChamaAdmin(admin.ModelAdmin):
    """Admin for Chama model."""
    
    list_display = ('group_name', 'registration_no', 'admin_id', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('group_name', 'registration_no')
    ordering = ('-created_at',)
    readonly_fields = ('chama_id', 'created_at', 'updated_at')


@admin.register(ChamaMember)
# For beginners: This class 'ChamaMemberAdmin' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'ChamaMemberAdmin' groups related data and behavior
# so other parts of the app can use one structured object.
class ChamaMemberAdmin(admin.ModelAdmin):
    """Admin for ChamaMember model."""
    
    list_display = ('user_id', 'chama_id', 'member_role', 'status', 'joined_at')
    list_filter = ('member_role', 'status', 'joined_at')
    search_fields = ('user_id__full_name', 'chama_id__group_name')
    ordering = ('joined_at',)
    readonly_fields = ('membership_id', 'joined_at')
