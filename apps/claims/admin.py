# For beginners: This file (apps/claims/admin.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

from django.contrib import admin
from django.utils import timezone
from .models import Claim, Notification


@admin.register(Claim)
# For beginners: This class 'ClaimAdmin' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'ClaimAdmin' groups related data and behavior
# so other parts of the app can use one structured object.
class ClaimAdmin(admin.ModelAdmin):
    list_display = ('claim_id', 'user_id', 'claim_type', 'claim_amount', 'status', 'ai_flagged', 'submitted_at')
    list_filter = ('claim_type', 'status', 'ai_flagged')
    search_fields = ('user_id__full_name', 'user_id__email', 'description')
    ordering = ('-submitted_at',)
    readonly_fields = ('claim_id', 'submitted_at', 'decided_at', 'paid_at', 'ai_verification', 'blockchain_hash', 'blockchain_tx')
    actions = ['approve_claims', 'reject_claims']

    fieldsets = (
        ('Claim Info', {
            'fields': ('claim_id', 'user_id', 'plan_id', 'claim_type', 'claim_amount', 'description')
        }),
        ('Status', {
            'fields': ('status', 'reviewed_by', 'decision_reason')
        }),
        ('AI & Blockchain', {
            'fields': ('ai_verification', 'ai_flagged', 'blockchain_hash', 'blockchain_tx'),
            'classes': ('collapse',)
        }),
        ('Payout', {
            'fields': ('payout_mpesa_ref',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'decided_at', 'paid_at'),
            'classes': ('collapse',)
        }),
    )

    # For beginners: This function 'approve_claims' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'approve_claims' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def approve_claims(self, request, queryset):
        queryset.update(
            status='approved',
            reviewed_by=request.user,
            decided_at=timezone.now()
        )
        self.message_user(request, f"{queryset.count()} claim(s) approved.")
    approve_claims.short_description = "Approve selected claims"

    # For beginners: This function 'reject_claims' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'reject_claims' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def reject_claims(self, request, queryset):
        queryset.update(
            status='rejected',
            reviewed_by=request.user,
            decided_at=timezone.now()
        )
        self.message_user(request, f"{queryset.count()} claim(s) rejected.")
    reject_claims.short_description = "Reject selected claims"


@admin.register(Notification)
# For beginners: This class 'NotificationAdmin' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'NotificationAdmin' groups related data and behavior
# so other parts of the app can use one structured object.
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'message', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('recipient__full_name', 'recipient__email', 'message')
    ordering = ('-created_at',)
    readonly_fields = ('notification_id', 'created_at')
