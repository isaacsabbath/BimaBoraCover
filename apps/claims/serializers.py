# For beginners: This file (apps/claims/serializers.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

"""
Serializers for Insurance Claims.
"""

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils import timezone
from rest_framework import serializers

from apps.users.services.mongo_storage import MongoAtlasStorageService
from .models import Claim


# For beginners: This class 'ClaimListSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'ClaimListSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
class ClaimListSerializer(serializers.ModelSerializer):
    """Serializer for listing claims."""
    
    user_email = serializers.CharField(source='user_id.email', read_only=True)
    plan_name = serializers.CharField(source='plan_id.plan_name', read_only=True)
    
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    class Meta:
        model = Claim
        fields = [
            'claim_id', 'user_email', 'plan_name', 'claim_type',
            'claim_amount', 'status', 'ai_flagged', 'submitted_at'
        ]
        read_only_fields = [
            'claim_id', 'user_email', 'plan_name', 'submitted_at'
        ]


# For beginners: This class 'ClaimDetailSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'ClaimDetailSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
class ClaimDetailSerializer(serializers.ModelSerializer):
    """Serializer for claim details."""
    
    user_email = serializers.CharField(source='user_id.email', read_only=True)
    plan_name = serializers.CharField(source='plan_id.plan_name', read_only=True)
    reviewed_by_name = serializers.CharField(
        source='reviewed_by.full_name', read_only=True, allow_null=True
    )
    
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    class Meta:
        model = Claim
        fields = [
            'claim_id', 'user_id', 'user_email', 'plan_id', 'plan_name',
            'claim_type', 'claim_amount', 'description', 'documents',
            'ai_verification', 'ai_flagged', 'status', 'reviewed_by',
            'reviewed_by_name', 'decision_reason', 'payout_mpesa_ref',
            'blockchain_hash', 'blockchain_tx', 'submitted_at', 'decided_at',
            'paid_at'
        ]
        read_only_fields = [
            'claim_id', 'user_id', 'ai_verification', 'blockchain_hash',
            'blockchain_tx', 'submitted_at'
        ]


# For beginners: This class 'ClaimSubmitSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'ClaimSubmitSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
class ClaimSubmitSerializer(serializers.ModelSerializer):
    """Serializer for submitting new claim."""
    
    documents = serializers.ListField(
        child=serializers.FileField(),
        required=True,
        help_text="Up to 5 supporting documents"
    )
    
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    class Meta:
        model = Claim
        fields = [
            'plan_id', 'claim_type', 'claim_amount', 'description', 'documents'
        ]
    
    # For beginners: This function 'validate_documents' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'validate_documents' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def validate_documents(self, value):
        """Validate document count and size."""
        if len(value) > 5:
            raise serializers.ValidationError("Maximum 5 documents allowed")
        
        for doc in value:
            if doc.size > 5 * 1024 * 1024:  # 5MB max
                raise serializers.ValidationError(f"File too large: {doc.name}")
        
        return value
    
    # For beginners: This function 'validate_description' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'validate_description' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def validate_description(self, value):
        """Description must be at least 50 characters."""
        if len(value) < 50:
            raise serializers.ValidationError("Description must be at least 50 characters")
        return value
    
    # For beginners: This function 'validate_claim_amount' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'validate_claim_amount' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def validate_claim_amount(self, value):
        """Claim amount must be positive."""
        if value <= 0:
            raise serializers.ValidationError("Claim amount must be positive")
        return value
    
    # For beginners: This function 'create' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'create' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def create(self, validated_data):
        """Create claim with current user."""
        documents = validated_data.pop('documents', [])
        validated_data['user_id'] = self.context['request'].user
        validated_data['status'] = 'submitted'

        storage_service = MongoAtlasStorageService()
        stored_documents = []
        for document in documents:
            # storage_path = default_storage.save(  # Azure/default-storage path kept for review
            #     f'claims/{validated_data["user_id"].id}/{document.name}',
            #     ContentFile(document.read())
            # )
            document_url = storage_service.upload_kyc_document(
                file_obj=document,
                document_type='claim-supporting-document',
                user_id=validated_data['user_id'].id,
                filename=document.name,
            )
            stored_documents.append({
                'label': document.name,
                'url': document_url,
            })

        validated_data['documents'] = stored_documents

        claim = Claim.objects.create(**validated_data)
        
        # Process documents with Azure AI Document Intelligence
        from apps.claims.views import await_ai_analysis
        await_ai_analysis(claim, documents)
        
        return claim


# For beginners: This class 'ClaimReviewSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'ClaimReviewSerializer' groups related data and behavior
# so other parts of the app can use one structured object.
class ClaimReviewSerializer(serializers.ModelSerializer):
    """Serializer for claims officer review."""
    
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    # For beginners: This class 'Meta' groups related data and behavior
    # so other parts of the app can use one structured object.
    class Meta:
        model = Claim
        fields = ['status', 'decision_reason']
    
    # For beginners: This function 'validate' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'validate' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def validate(self, data):
        """Validate claim can be reviewed."""
        claim = self.instance
        
        if claim.status not in ['submitted', 'info_requested']:
            raise serializers.ValidationError(
                f"Can only review submitted/info_requested claims, not {claim.status}"
            )
        
        if data['status'] not in ['approved', 'rejected', 'info_requested']:
            raise serializers.ValidationError(
                "Status must be approved, rejected, or info_requested"
            )
        
        if data['status'] in ['approved', 'rejected'] and not data.get('decision_reason'):
            raise serializers.ValidationError(
                "Decision reason required for approval/rejection"
            )
        
        return data
    
    # For beginners: This function 'update' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'update' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def update(self, instance, validated_data):
        """Update claim with review."""
        instance.status = validated_data['status']
        instance.decision_reason = validated_data.get('decision_reason')
        instance.reviewed_by = self.context['request'].user
        instance.decided_at = timezone.now()
        instance.save()
        return instance
