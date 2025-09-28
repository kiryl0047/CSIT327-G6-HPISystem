from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse
from .forms import LoginForm, SignupForm, DirectPasswordResetForm


# Create your views here.
def index(response):
    return HttpResponse("<h1>LET'S GO!!!</h1>")

def user_login(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data['username']  # can be username or email
            password = form.cleaned_data['password']

            # Try to find the user by username or email
            try:
                user_obj = User.objects.get(username__iexact=identifier)
            except User.DoesNotExist:
                try:
                    user_obj = User.objects.get(email__iexact=identifier)
                except User.DoesNotExist:
                    messages.error(request, "User not found.")
                    return render(request, "login.html", {"form": form})

            # Authenticate using the username
            user = authenticate(request, username=user_obj.username, password=password)

            if user is not None:
                login(request, user)  # creates session
                return render(request, "homepage.html", {"username": user.username})
            else:
                messages.error(request, "Incorrect password.")
    else:
        form = LoginForm()

    return render(request, "login.html", {"form": form})

# Signup View
def signup(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()  # This automatically saves to your Supabase DB
            username = form.cleaned_data.get("username")
            messages.success(request, f"Account created for {username}. You can now login.")
            return redirect("user_login")  # make sure this matches your login URL name
    else:
        form = SignupForm()
    return render(request, "signup.html", {"form": form})

# Password Reset View
def password_reset(request):
    if request.method == "POST":
        form = DirectPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            new_password1 = form.cleaned_data["new_password1"]
            new_password2 = form.cleaned_data["new_password2"]

            if new_password1 != new_password2:
                messages.error(request, "Passwords do not match.")
                return render(request, "password_reset.html", {"form": form})

            try:
                user = User.objects.get(email=email)
                user.set_password(new_password1)
                user.save()
                messages.success(request, "Your password has been updated. You can now log in.")
                return redirect("user_login")
            except User.DoesNotExist:
                messages.error(request, "No account found with that email.")
    else:
        form = DirectPasswordResetForm()

    return render(request, "password_reset.html", {"form": form})