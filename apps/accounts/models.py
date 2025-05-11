from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.urls import reverse
import uuid

class Profile(models.Model):
    SUBSCRIPTION_TYPES = [
        ("F", "Basic"),
        ("P", "Pro"),
        ("B", "Business"),
        ("E", "Enterprise"),
     ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='profile_pics/', null=True, blank=True, verbose_name="Profile Picture")
    subscription_type = models.CharField(max_length=100, choices=SUBSCRIPTION_TYPES, null=True, default='F')
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
class CollaborationGroup(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=400,blank=True, null=True)
    members = models.ManyToManyField(User, related_name='collaboration_groups')
    created_at = models.DateTimeField(auto_now_add=True)
    dataset = models.ManyToManyField('DataRecordOrDataset', blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    def __str__(self):
        return self.name

class CompanyInvite(models.Model):
    email = models.EmailField()
    name = models.CharField(max_length=255)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    collaboration_group = models.ForeignKey(CollaborationGroup, on_delete=models.CASCADE)
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invites')
    created_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)
    rejected = models.BooleanField(default=False)
    expiration_date = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expiration_date

    def get_accept_url(self):
        return reverse('accept_invite', kwargs={'token': self.token})

    def get_reject_url(self):
        return reverse('reject_invite', kwargs={'token': self.token})

    def __str__(self):
        return f"Invite to {self.email}"
    

class DataRecordOrDataset(models.Model):
    STATUS = [
        ("P", "Plain Data"),
        ("E", "Encrypted Data"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recorded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=100 ,choices=STATUS,default='P')
    file = models.FileField(upload_to='uploads/',null=True)  # Add this line
    collaboration_groups = models.ManyToManyField(CollaborationGroup,blank=True)
    def filename(self):
        return self.file.name.split('/')[-1] if self.file else 'Unnamed'

    def uploaded_date(self):
        return self.recorded_at.strftime('%Y-%m-%d %H:%M')

    def size(self):
        return f"{self.file.size / 1024:.2f} KB" if self.file else "0 KB"


class AnalysisReport(models.Model):
    record = models.OneToOneField(DataRecordOrDataset, on_delete=models.CASCADE)
    analysis_result = models.TextField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    shap_plot = models.ImageField(upload_to='shap_plots/', null=True, blank=True)

class EncryptionKey(models.Model):
    record = models.OneToOneField(DataRecordOrDataset, on_delete=models.CASCADE)
    key_value = models.CharField(unique=True,max_length=255)


class CustomerOrUserReview(models.Model):
    REVIEW_STATUS = [
        ("P", "Pending"),
        ("A", "Approved"),
        ("R", "Rejected"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField(blank=True , null=True)
    submit_at = models.DateTimeField(auto_now_add=True)
    review_status = models.CharField(max_length=100 ,choices= REVIEW_STATUS,default='P')

class AdminOrEmployee(models.Model):
    ROLE_TYPES = [
    ("D", "Web Developer"),
    ("S", "Syper Security Member"),
    ("E", "Employee"),
    ]
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=100 , choices= ROLE_TYPES,default='E')

class AuthenticationLog(models.Model):
    LOG_STATUS = [
        ("F", "Failed"),
        ("S", "Success"),
    ]
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    admin = models.ForeignKey(AdminOrEmployee, on_delete=models.SET_NULL, null=True, blank=True)
    log_time = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_info = models.CharField(max_length=255,null=True, blank=True)
    log_status = models.CharField(max_length=100 ,choices= LOG_STATUS,default='S')

    
class Audit(models.Model):
    ACTION_TYPES = [
        ("E", "Encryption"),
        ("D", "Decryption"),
        ("A", "Analysis"),
        ("C", "Collaporation"), 
    ]
    #user = models.ForeignKey(UnicodeTranslateError, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    admin = models.ForeignKey(AdminOrEmployee, on_delete=models.SET_NULL, null=True, blank=True)
    action_type = models.CharField(max_length=255 ,choices= ACTION_TYPES)
    record = models.ForeignKey(DataRecordOrDataset, on_delete=models.SET_NULL, null=True, blank=True)
    audit_time = models.DateTimeField(auto_now_add=True)