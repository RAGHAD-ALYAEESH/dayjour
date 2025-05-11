# accounts/signals.py
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import AuthenticationLog
from django.db.models.signals import post_save
from django.conf import settings
from .models import Profile, CompanyInvite, CollaborationGroup
from django.utils import timezone

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    ip_address = request.META.get('REMOTE_ADDR')
    AuthenticationLog.objects.create(user=user, ip_address=ip_address)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def connect_invite_to_user(sender, instance, created, **kwargs):
    if created:
        try:
            invite = CompanyInvite.objects.get(email=instance.email, accepted=True, rejected=False)

            if invite.is_expired():
                # Invite is expired ➔ mark as rejected
                invite.rejected = True
                invite.save()
                print(f"[INFO] Invite for {instance.email} was expired and marked as rejected.")
            else:
                # Invite is still valid ➔ accept and connect
                invite.accepted = True
                invite.save()
                invite.collaboration_group.members.add(instance)
                print(f"[INFO] User {instance.email} connected to invitation and added to collaboration group.")

        except CompanyInvite.DoesNotExist:
            print(f"[INFO] No pending invitation for {instance.email}")