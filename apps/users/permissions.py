"""
Role-Based Access Control (RBAC) permission classes.
"""

from rest_framework import permissions


class IsSuperAdmin(permissions.BasePermission):
    """Permission class for super admin users."""
    
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'super_admin'
        )


class IsClaimsOfficer(permissions.BasePermission):
    """Permission class for claims officer users."""
    
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'claims_officer'
        )


class IsChamaAdmin(permissions.BasePermission):
    """Permission class for Chama admin users."""
    
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'chama_admin'
        )


class IsChamaMember(permissions.BasePermission):
    """Permission class for Chama member users."""
    
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'chama_member'
        )


class IsIndividual(permissions.BasePermission):
    """Permission class for individual users."""
    
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'individual'
        )


class IsKYCVerified(permissions.BasePermission):
    """Permission to ensure user has completed KYC verification."""
    
    message = 'Your identity must be verified before accessing this resource. Please complete KYC.'
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.kyc_status == 'verified'


class IsOwnerOrAdmin(permissions.BasePermission):
    """Permission to check if user is owner of object or admin."""
    
    def has_object_permission(self, request, view, obj):
        # Allow admins
        if request.user.role in ['super_admin', 'claims_officer']:
            return True
        
        # Check if user is owner
        if hasattr(obj, 'user_id'):
            return obj.user_id == request.user.id
        if hasattr(obj, 'user'):
            return obj.user.id == request.user.id
        
        return False
