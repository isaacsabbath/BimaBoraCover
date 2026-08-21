# For beginners: This file (apps/chamas/views.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

"""
Views for Chama (group) management endpoints.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.urls import reverse
import uuid
from django.core.cache import cache
from apps.chamas.tasks import queue_chama_invite_email, queue_chama_invite_sms
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.chamas.models import Chama, ChamaMember
from apps.chamas.serializers import (
    ChamaListSerializer, ChamaDetailSerializer, ChamaCreateUpdateSerializer, ChamaMemberSerializer
)


# For beginners: This class 'ChamaViewSet' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'ChamaViewSet' groups related data and behavior
# so other parts of the app can use one structured object.
class ChamaViewSet(viewsets.ModelViewSet):
    """ViewSet for Chama CRUD operations and invitations."""
    
    permission_classes = [IsAuthenticated]
    lookup_field = 'chama_id'
    
    # For beginners: This function 'get_serializer_class' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'get_serializer_class' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ChamaListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ChamaCreateUpdateSerializer
        else:
            return ChamaDetailSerializer
    
    # For beginners: This function 'get_queryset' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'get_queryset' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def get_queryset(self):
        """Return Chamas the user is member of."""
        from apps.users.models import User
        user = self.request.user
        # Get all chamas the user is a member of
        chama_ids = ChamaMember.objects.filter(
            user_id=user, status='active'
        ).values_list('chama_id', flat=True)
        return Chama.objects.filter(chama_id__in=chama_ids).order_by('-created_at')
    
    # For beginners: This function 'create' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'create' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def create(self, request, *args, **kwargs):
        """Create a new Chama (current user becomes admin)."""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    # For beginners: This function 'perform_update' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'perform_update' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def perform_update(self, serializer):
        """Ensure only admin can update chama."""
        chama_id = self.kwargs.get('chama_id')
        chama = Chama.objects.get(chama_id=chama_id)
        
        if self.request.user != chama.admin_id:
            raise PermissionError("Only Chama admin can update")
        serializer.save()
    
    @action(detail=True, methods=['post'], url_path='invite')
    # For beginners: This function 'send_invite' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'send_invite' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def send_invite(self, request, chama_id=None):
        """Send invitation to a new member (admin only)."""
        chama = self.get_object()
        
        # Verify user is admin
        if request.user != chama.admin_id:
            return Response(
                {'error': 'Only Chama admin can invite members'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get email from request
        email = request.data.get('email')
        if not email:
            return Response(
                {'error': 'Email required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if email exists and not already in chama
        from apps.users.models import User
        try:
            invite_user = User.objects.get(email=email)
            
            # Check if already member
            if ChamaMember.objects.filter(chama_id=chama, user_id=invite_user).exists():
                return Response(
                    {'error': 'User already a member'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Generate invite token (UUID + 48hr expiry)
        token = str(uuid.uuid4())
        cache.set(
            f'chama_invite:{token}',
            {'chama_id': str(chama_id), 'user_id': str(invite_user.user_id), 'email': email},
            timeout=48 * 3600  # 48 hours
        )

        invite_link = request.build_absolute_uri(
            reverse('chama_invite_accept', args=[token])
        )
        queue_chama_invite_email(
            email=email,
            chama_name=chama.group_name,
            invite_link=invite_link,
            inviter_name=request.user.full_name,
        )
        if invite_user.phone_number:
            queue_chama_invite_sms(
                phone_number=invite_user.phone_number,
                chama_name=chama.group_name,
                invite_link=invite_link,
                inviter_name=request.user.full_name,
            )

        return Response({
            'message': 'Invitation sent',
            'token': token,
            'expires_in_hours': 48
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'], url_path='join/(?P<token>[^/.]+)')
    # For beginners: This function 'join_via_token' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'join_via_token' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def join_via_token(self, request, token=None):
        """Accept invitation and join Chama."""
        # Get invite from cache
        invite_data = cache.get(f'chama_invite:{token}')
        
        if not invite_data:
            return Response(
                {'error': 'Invalid or expired token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify user matches
        if str(request.user.user_id) != invite_data['user_id']:
            return Response(
                {'error': 'Token belongs to different user'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Add user to chama
        chama = Chama.objects.get(chama_id=invite_data['chama_id'])
        member, created = ChamaMember.objects.get_or_create(
            chama_id=chama,
            user_id=request.user,
            defaults={'status': 'active'}
        )
        
        if not created:
            member.status = 'active'
            member.save()
        
        # Invalidate token
        cache.delete(f'chama_invite:{token}')
        
        serializer = ChamaDetailSerializer(chama, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['delete'], url_path='members/(?P<user_id>[^/.]+)')
    # For beginners: This function 'remove_member' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'remove_member' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def remove_member(self, request, chama_id=None, user_id=None):
        """Remove member from Chama (admin only)."""
        chama = self.get_object()
        
        # Verify user is admin
        if request.user != chama.admin_id:
            return Response(
                {'error': 'Only Chama admin can remove members'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate UUID format
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            return Response(
                {'error': 'Invalid user ID'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Cannot remove admin
        if request.user.user_id == user_uuid:
            return Response(
                {'error': 'Cannot remove yourself (admin)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Remove member
        try:
            member = ChamaMember.objects.get(chama_id=chama, user_id__user_id=user_uuid)
            member.delete()
            return Response(
                {'message': f'Member {user_id} removed'},
                status=status.HTTP_204_NO_CONTENT
            )
        except ChamaMember.DoesNotExist:
            return Response(
                {'error': 'Member not found'},
                status=status.HTTP_404_NOT_FOUND
            )


# ─── Template Views ───────────────────────────────────────────────────────────

@login_required(login_url='login')
# For beginners: This function 'chama_page' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
# For beginners: This function 'chama_page' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
def chama_page(request):
    chama_ids = ChamaMember.objects.filter(user_id=request.user, status='active').values_list('chama_id', flat=True)
    chamas = Chama.objects.filter(chama_id__in=chama_ids).prefetch_related('members')
    return render(request, 'chamas/list.html', {'chamas': chamas})


@login_required(login_url='login')
# For beginners: This function 'chama_detail_page' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
# For beginners: This function 'chama_detail_page' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
def chama_detail_page(request, chama_id):
    chama = get_object_or_404(Chama, chama_id=chama_id)
    members = ChamaMember.objects.filter(chama_id=chama, status='active').select_related('user_id')
    return render(request, 'chamas/detail.html', {'chama': chama, 'members': members})


@login_required(login_url='login')
@require_POST
# For beginners: This function 'chama_create_page' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
# For beginners: This function 'chama_create_page' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
def chama_create_page(request):
    chama = Chama.objects.create(
        group_name=request.POST['group_name'],
        registration_no=request.POST['registration_no'],
        expected_members=int(request.POST.get('expected_members', 2)),
        admin_id=request.user, status='active',
    )
    ChamaMember.objects.create(chama_id=chama, user_id=request.user, member_role='admin', status='active')
    messages.success(request, f'Chama "{chama.group_name}" created successfully!')
    return redirect('chama')


@login_required(login_url='login')
@require_POST
# For beginners: This function 'chama_invite_page' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
# For beginners: This function 'chama_invite_page' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
def chama_invite_page(request):
    from apps.users.models import User
    chama = get_object_or_404(Chama, chama_id=request.POST.get('chama_id'), admin_id=request.user)
    try:
        invite_user = User.objects.get(email=request.POST.get('email'))
        ChamaMember.objects.get_or_create(
            chama_id=chama, user_id=invite_user,
            defaults={'status': 'active', 'member_role': 'member'}
        )
        messages.success(request, f'{invite_user.full_name} added to {chama.group_name}.')
    except User.DoesNotExist:
        messages.error(request, 'No user found with that email.')
    return redirect('chama')


@login_required(login_url='login')
# For beginners: This function 'chama_invite_accept_page' performs one
# reusable task — it's the page the invitee lands on when they click the
# link in the invite email, since the DRF join_via_token action is a
# POST-only API endpoint and isn't something a browser link can hit directly.
def chama_invite_accept_page(request, token):
    """GET: show invite details with an Accept button.
    POST: join the chama and redirect to it."""
    invite_data = cache.get(f'chama_invite:{token}')

    if not invite_data:
        messages.error(request, 'This invite link is invalid or has expired.')
        return redirect('chama')

    chama = get_object_or_404(Chama, chama_id=invite_data['chama_id'])

    # The invite was issued for a specific email/user — if the logged-in
    # user doesn't match, don't silently add the wrong account.
    if str(request.user.user_id) != invite_data['user_id']:
        messages.error(
            request,
            f"This invite was sent to {invite_data['email']}. "
            f"Please log in with that account to accept it."
        )
        return redirect('chama')

    if request.method == 'POST':
        member, created = ChamaMember.objects.get_or_create(
            chama_id=chama,
            user_id=request.user,
            defaults={'status': 'active'}
        )
        if not created:
            member.status = 'active'
            member.save(update_fields=['status'])

        cache.delete(f'chama_invite:{token}')
        messages.success(request, f'You joined {chama.group_name}!')
        return redirect('chama')

    return render(request, 'chamas/invite_accept.html', {'chama': chama, 'token': token})
