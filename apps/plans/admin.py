# For beginners: This file (apps/plans/admin.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

from django.contrib import admin
from .models import InsurancePlan, Policy


@admin.register(InsurancePlan)
# For beginners: This class 'InsurancePlanAdmin' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'InsurancePlanAdmin' groups related data and behavior
# so other parts of the app can use one structured object.
class InsurancePlanAdmin(admin.ModelAdmin):
    list_display = ('plan_name', 'coverage_category', 'plan_type', 'status', 'base_rate', 'created_at')
    list_filter = ('coverage_category', 'plan_type', 'status')
    search_fields = ('plan_name',)
    ordering = ('-created_at',)
    readonly_fields = ('plan_id', 'created_at')

    # For beginners: This function 'save_model' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'save_model' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    # For beginners: This function 'get_fields' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'get_fields' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def get_fields(self, request, obj=None):
        fields = [
            'plan_name', 'plan_type', 'coverage_category',
            'base_rate', 'min_coverage', 'max_coverage',
            'duration_days', 'payment_frequency', 'status',
        ]
        if obj:
            fields = ['plan_id', 'created_at'] + fields
        return fields


@admin.register(Policy)
# For beginners: This class 'PolicyAdmin' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'PolicyAdmin' groups related data and behavior
# so other parts of the app can use one structured object.
class PolicyAdmin(admin.ModelAdmin):
    list_display = ('policy_id', 'user_id', 'plan_id', 'coverage_amount', 'status', 'start_date')
    list_filter = ('status',)
    search_fields = ('user_id__full_name', 'user_id__email', 'payment_reference')
    ordering = ('-created_at',)
    readonly_fields = ('policy_id', 'created_at', 'updated_at', 'start_date')
