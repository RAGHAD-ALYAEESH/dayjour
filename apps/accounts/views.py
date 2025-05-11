from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from apps.accounts.forms import ProfileImageForm
from apps.accounts.models import Profile
from django.contrib.auth.models import User


@login_required(login_url='/en/login/')
def account_settings(request):
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        image_form = ProfileImageForm(request.POST, request.FILES, instance=profile)

        user.username = username
        user.email = email
        if password:
            user.set_password(password)
            update_session_auth_hash(request, user)
        user.save()

        if image_form.is_valid():
            image_form.save()

        messages.success(request, "Account updated successfully!")
        return redirect('account_settings')

    image_form = ProfileImageForm(instance=profile)
    return render(request, 'account_settings.html', {
        'user': user,
        'image_form': image_form
    })


@login_required
def profile(request):
    Profile.objects.get_or_create(user=request.user)
    return render(request, 'profile.html')


def logout_view(request):
    logout(request)
    return redirect('home')