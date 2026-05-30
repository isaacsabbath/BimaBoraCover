from django.contrib import admin
from .models import Payment


@admin.register(Payment)
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
