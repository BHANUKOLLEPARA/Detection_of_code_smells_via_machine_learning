"""
Accounts App Views
"""

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Profile, UserActivity
import secrets


def register_view(request):
    """User registration view"""
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        # Validation
        if not username or not email or not password1 or not password2:
            messages.error(request, "All fields are required!")
            return redirect("accounts:register")

        if password1 != password2:
            messages.error(request, "Passwords do not match!")
            return redirect("accounts:register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
            return redirect("accounts:register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return redirect("accounts:register")

        # Create user
        user = User.objects.create_user(
            username=username, email=email, password=password1
        )

        # Generate API key
        api_key = secrets.token_urlsafe(32)

        if hasattr(user, "profile"):
            user.profile.api_key = api_key
            user.profile.save()

        messages.success(request, "Registration successful! Please login.")
        return redirect("accounts:login")

    return render(request, "accounts/register.html")


def login_view(request):
    """User login view"""
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {username}!")
            return redirect("detector:dashboard")
        else:
            messages.error(request, "Invalid username or password!")

    return render(request, "accounts/login.html")


def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect("index")


@login_required
def profile_view(request):
    """User profile view"""
    if request.method == "POST":

        user = request.user

        user.first_name = request.POST.get("first_name", "")
        user.last_name = request.POST.get("last_name", "")
        user.email = request.POST.get("email", "")
        user.save()

        if hasattr(user, "profile"):

            profile = user.profile

            profile.bio = request.POST.get("bio", "")
            profile.location = request.POST.get("location", "")

            if "profile_pic" in request.FILES:
                profile.profile_pic = request.FILES["profile_pic"]

            profile.save()

        messages.success(request, "Profile updated successfully!")
        return redirect("accounts:profile")

    activities = []

    if hasattr(UserActivity, "objects"):
        activities = UserActivity.objects.filter(user=request.user)[:10]

    context = {"activities": activities}

    return render(request, "accounts/profile.html", context)
