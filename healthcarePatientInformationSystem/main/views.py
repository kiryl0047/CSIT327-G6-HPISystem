from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse
from .forms import LoginForm, SignupForm


# Create your views here.
def user_login(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data['username']  # can be username or email
            password = form.cleaned_data['password']
            try:
                user_obj = User.objects.get(username__iexact=identifier)
            except User.DoesNotExist:
                try:
                    user_obj = User.objects.get(email__iexact=identifier)
                except User.DoesNotExist:
                    messages.error(request, "User not found.")
                    return render(request, "login.html", {"form": form})

            user = authenticate(request, username=user_obj.username, password=password)

            if user is not None:
                login(request, user)
                if not request.POST.get("remember_me"):
                    request.session.set_expiry(0)
                else:
                    request.session.set_expiry(1209600)

                return redirect("homepage")
            else:
                messages.error(request, "Incorrect password.")
    else:
        form = LoginForm()

    return render(request, "login.html", {"form": form})

@login_required
def homepage(request):
    recent_activity = [
        "9/26/25: Your appointment with Dr. Banyo is confirmed.",
        "9/26/25: Your appointment with Mr. Discaya is confirmed.",
        "9/26/25: Your appointment with Engr. Hernandez is confirmed.",
        "9/26/25: Your appointment with Engr. Alcantara is confirmed.",
    ]
    return render(request, "homepage.html", {
        "username": request.user.username,
        "recent_activity": recent_activity
    })

@login_required
def book_appointment(request):
    if request.method == "POST":
        # Handle appointment booking here
        patient = request.user
        doctor = request.POST.get("doctor")
        date = request.POST.get("date")
        time = request.POST.get("time")
        # Save to database (example only, depends on your model)
        # Appointment.objects.create(patient=patient, doctor=doctor, date=date, time=time)
        return redirect("upcoming_appointments")
    return render(request, "book_appointment.html")

@login_required
def upcoming_appointments(request):
    # Example: Fetch appointments from DB
    # appointments = Appointment.objects.filter(patient=request.user)
    appointments = [
        {"doctor": "Dr. Banyo", "date": "2025-10-05", "time": "10:00 AM"},
        {"doctor": "Dr. Hernandez", "date": "2025-10-07", "time": "2:30 PM"},
    ]
    return render(request, "upcoming_appointments.html", {"appointments": appointments})

@login_required
def request_prescription(request):
    if request.method == "POST":
        # Handle prescription request
        medication = request.POST.get("medication")
        notes = request.POST.get("notes")
        # PrescriptionRequest.objects.create(patient=request.user, medication=medication, notes=notes)
        return redirect("homepage")
    return render(request, "request_prescription.html")

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
