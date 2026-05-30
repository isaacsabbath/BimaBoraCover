"""
Serializers for Chama (group) management.
"""

from rest_framework import serializers
from apps.chamas.models import Chama, ChamaMember
from apps.users.models import User


class ChamaMemberDetailSerializer(serializers.ModelSerializer):
    """Serializer for Chama members with user details."""
    
    user_email = serializers.CharField(source='user_id.email', read_only=True)
    user_full_name = serializers.CharField(source='user_id.full_name', read_only=True)
    user_phone = serializers.CharField(source='user_id.phone_number', read_only=True)
    
    class Meta:
        model = ChamaMember
        fields = ['membership_id', 'user_id', 'user_email', 'user_full_name', 'user_phone', 'status', 'joined_at']
        read_only_fields = ['membership_id', 'user_id', 'joined_at']


class ChamaDetailSerializer(serializers.ModelSerializer):
    """Serializer for Chama detail view with full member list."""
    
    admin_email = serializers.CharField(source='admin_id.email', read_only=True)
    admin_full_name = serializers.CharField(source='admin_id.full_name', read_only=True)
    members = ChamaMemberDetailSerializer(many=True, source='chamaMember_set', read_only=True)
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Chama
        fields = ['chama_id', 'chama_name', 'description', 'admin_id', 'admin_email', 'admin_full_name', 
                  'status', 'created_at', 'members', 'member_count']
        read_only_fields = ['chama_id', 'admin_id', 'created_at']
    
    def get_member_count(self, obj):
        return obj.chamaMember_set.filter(status='active').count()


class ChamaCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating a Chama."""
    
    class Meta:
        model = Chama
        fields = ['chama_name', 'description', 'status']
    
    def create(self, validated_data):
        """Create Chama with current user as admin."""
        validated_data['admin_id'] = self.context['request'].user
        chama = Chama.objects.create(**validated_data)
        # Auto-add admin as first member
        ChamaMember.objects.create(chama_id=chama, user_id=self.context['request'].user, status='active')
        return chama


class ChamaListSerializer(serializers.ModelSerializer):
    """Serializer for Chama list view (minimal data)."""
    
    admin_full_name = serializers.CharField(source='admin_id.full_name', read_only=True)
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Chama
        fields = ['chama_id', 'chama_name', 'admin_full_name', 'status', 'member_count', 'created_at']
        read_only_fields = ['chama_id', 'created_at']
    
    def get_member_count(self, obj):
        return obj.chamaMember_set.filter(status='active').count()


class ChamaMemberSerializer(serializers.ModelSerializer):
    """Serializer for ChamaMember model."""
    
    class Meta:
        model = ChamaMember
        fields = ['membership_id', 'chama_id', 'user_id', 'status', 'joined_at']
        read_only_fields = ['membership_id', 'joined_at']
