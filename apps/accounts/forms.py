from django import forms
from .models import Profile
from django.contrib.auth import get_user_model

User = get_user_model()

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']

class ProfileImageForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image']