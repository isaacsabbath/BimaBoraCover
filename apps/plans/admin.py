from django.contrib import admin
from .models import InsurancePlan, Policy


@admin.register(InsurancePlan)
class InsurancePlanAdmin(admin.ModelAdmin):
    list_display = ('plan_name', 'coverage_category', 'plan_type', 'status', 'base_rate', 'created_at')
    list_filter = ('coverage_category', 'plan_type', 'status')
    search_fields = ('plan_name',)
    ordering = ('-created_at',)
    readonly_fields = ('plan_id', 'created_at')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

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
class PolicyAdmin(admin.ModelAdmin):
    list_display = ('policy_id', 'user_id', 'plan_id', 'coverage_amount', 'status', 'start_date')
    list_filter = ('status',)
    search_fields = ('user_id__full_name', 'user_id__email', 'payment_reference')
    ordering = ('-created_at',)
    readonly_fields = ('policy_id', 'created_at', 'updated_at', 'start_date')
