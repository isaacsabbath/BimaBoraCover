# For beginners: This file (apps/users/permissions.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

"""
Role-Based Access Control (RBAC) permission classes.
"""

from rest_framework import permissions


# For beginners: This class 'IsSuperAdmin' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'IsSuperAdmin' groups related data and behavior
# so other parts of the app can use one structured object.
class IsSuperAdmin(permissions.BasePermission):
    """Permission class for super admin users."""
    
    # For beginners: This function 'has_permission' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'has_permission' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'super_admin'
        )


# For beginners: This class 'IsClaimsOfficer' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'IsClaimsOfficer' groups related data and behavior
# so other parts of the app can use one structured object.
class IsClaimsOfficer(permissions.BasePermission):
    """Permission class for claims officer users."""
    
    # For beginners: This function 'has_permission' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'has_permission' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'claims_officer'
        )


# For beginners: This class 'IsChamaAdmin' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'IsChamaAdmin' groups related data and behavior
# so other parts of the app can use one structured object.
class IsChamaAdmin(permissions.BasePermission):
    """Permission class for Chama admin users."""
    
    # For beginners: This function 'has_permission' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'has_permission' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'chama_admin'
        )


# For beginners: This class 'IsChamaMember' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'IsChamaMember' groups related data and behavior
# so other parts of the app can use one structured object.
class IsChamaMember(permissions.BasePermission):
    """Permission class for Chama member users."""
    
    # For beginners: This function 'has_permission' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'has_permission' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'chama_member'
        )


# For beginners: This class 'IsIndividual' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'IsIndividual' groups related data and behavior
# so other parts of the app can use one structured object.
class IsIndividual(permissions.BasePermission):
    """Permission class for individual users."""
    
    # For beginners: This function 'has_permission' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'has_permission' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'individual'
        )


# For beginners: This class 'IsKYCVerified' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'IsKYCVerified' groups related data and behavior
# so other parts of the app can use one structured object.
class IsKYCVerified(permissions.BasePermission):
    """Permission to ensure user has completed KYC verification."""
    
    message = 'Your identity must be verified before accessing this resource. Please complete KYC.'
    
    # For beginners: This function 'has_permission' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'has_permission' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.kyc_status == 'verified'


# For beginners: This class 'IsOwnerOrAdmin' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'IsOwnerOrAdmin' groups related data and behavior
# so other parts of the app can use one structured object.
class IsOwnerOrAdmin(permissions.BasePermission):
    """Permission to check if user is owner of object or admin."""
    
    # For beginners: This function 'has_object_permission' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'has_object_permission' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
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
