# core/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.models import User


def home(request):
    return render(request, "Blay/home.html")

def dashboard(request):
    return render(request, 'dashboard.html')

def user_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
        except User.DoesNotExist:
            user = None

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid email or password")

    return render(request, "login.html")

def signin_view(request):
    if request.method == "POST":
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        if not name or not email or not password:
            messages.error(request, "All fields are required.")
            return redirect('signup')

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Enter a valid email address.")
            return redirect('signup')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
            return redirect('signup')

        user = User(username=name, email=email)
        user.set_password(password)
        user.save()

        messages.success(request, "Account created successfully! You can now log in.")
        return redirect('dashboard')

    return render(request, 'signin.html')

