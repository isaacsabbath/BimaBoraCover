# For beginners: This file (apps/payments/admin.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

from django.contrib import admin
from .models import Payment


@admin.register(Payment)
# For beginners: This class 'PaymentAdmin' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'PaymentAdmin' groups related data and behavior
# so other parts of the app can use one structured object.
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'user_id', 'amount', 'payment_type', 'payment_direction', 'status', 'mpesa_ref', 'initiated_at')
    list_filter = ('payment_type', 'payment_direction', 'status')
    search_fields = ('user_id__full_name', 'user_id__email', 'mpesa_ref')
    ordering = ('-initiated_at',)
    readonly_fields = ('payment_id', 'initiated_at', 'confirmed_at')

    fieldsets = (
        ('Payment Info', {
            'fields': ('payment_id', 'user_id', 'plan_id', 'chama_id', 'amount', 'payment_type', 'payment_direction')
        }),
        ('M-Pesa', {
            'fields': ('mpesa_ref', 'status', 'failure_reason')
        }),
        ('Timestamps', {
            'fields': ('initiated_at', 'confirmed_at'),
            'classes': ('collapse',)
        }),
    )
