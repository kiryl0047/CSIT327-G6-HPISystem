from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse
from .forms import LoginForm


# Create your views here.
def index(response):
    return HttpResponse("<h1>LET'S GO!!!</h1>")

def user_login(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            return render(request, "homepage.html", {"username": username})
    else:
        form = LoginForm()

    return render(request, "login.html", {"form": form})

# Signup View
def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get("username")
            messages.success(request, f"Account created for {username}. You can now login.")
            return redirect("login")
    else:
        form = UserCreationForm()
    return render(request, "signup.html", {"form": form})

# Password Reset View
def password_reset(request):
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            # Normally, Django sends reset email here
            messages.success(request, "If an account exists, you will receive an email to reset your password.")
            return redirect("user_login")
    else:
        form = PasswordResetForm()
    return render(request, "password_reset.html", {"form": form})