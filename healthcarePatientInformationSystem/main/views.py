from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, FileResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from datetime import timedelta
import json
import csv
from io import BytesIO, StringIO
from django.db import connection

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django.http import HttpResponse

from .forms import LoginForm, SignupForm, UserProfileForm, CustomPasswordChangeForm, NotificationPreferencesForm

from .models import (
    UserProfile, NotificationPreference, AccessLog,
    DataExportRequest, DeleteAccountRequest
)


def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_access(user, access_type, description="", request=None):
    """Log user access for security tracking"""
    ip_address = get_client_ip(request) if request else None
    user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''

    AccessLog.objects.create(
        user=user,
        access_type=access_type,
        ip_address=ip_address,
        user_agent=user_agent,
        description=description
    )


@login_required
def settings_page(request):
    """Main settings page view"""
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user)

    try:
        notification_pref = request.user.notification_preference
    except NotificationPreference.DoesNotExist:
        notification_pref = NotificationPreference.objects.create(user=request.user)

    context = {
        'user_profile': user_profile,
        'notification_pref': notification_pref,
    }

    return render(request, 'settings.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def update_profile(request):
    """Handle user profile updates"""
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)

        if form.is_valid():
            user = form.save()
            user_profile.user_type = form.cleaned_data.get('user_type')
            user_profile.profession = form.cleaned_data.get('profession')
            user_profile.save()

            log_access(
                request.user,
                'data_update',
                'Updated profile information',
                request
            )

            messages.success(request, 'Profile updated successfully!')
            return redirect('settings')
        else:
            return render(request, 'settings.html', {'form': form, 'errors': form.errors})

    else:
        form = UserProfileForm(instance=request.user)
        form.initial['user_type'] = user_profile.user_type
        form.initial['profession'] = user_profile.profession

    return render(request, 'settings.html', {'form': form})


@login_required
@require_http_methods(["GET", "POST"])
def change_password(request):
    """Handle password change"""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)

        if form.is_valid():
            user = form.save()

            log_access(
                request.user,
                'data_update',
                'Changed password',
                request
            )

            messages.success(request, 'Password changed successfully!')
            return redirect('settings')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
            return redirect('settings')

    else:
        form = CustomPasswordChangeForm(request.user)

    return render(request, 'settings.html', {'password_form': form})


@login_required
@require_http_methods(["POST"])
def update_notifications(request):
    """Handle notification preference updates"""
    try:
        notification_pref = request.user.notification_preference
    except NotificationPreference.DoesNotExist:
        notification_pref = NotificationPreference.objects.create(user=request.user)

    if request.method == 'POST':
        form = NotificationPreferencesForm(request.POST)

        if form.is_valid():
            notification_pref.email_notifications = form.cleaned_data.get('email_notifications', True)
            notification_pref.sms_notifications = form.cleaned_data.get('sms_notifications', True)
            notification_pref.prescription_alerts = form.cleaned_data.get('prescription_alerts', True)
            notification_pref.system_updates = form.cleaned_data.get('system_updates', True)
            notification_pref.save()

            log_access(
                request.user,
                'data_update',
                'Updated notification preferences',
                request
            )

            messages.success(request, 'Notification preferences updated successfully!')

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success', 'message': 'Updated successfully'})

            return redirect('settings')

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@login_required
def access_logs(request):
    """Display user access logs"""
    logs = AccessLog.objects.filter(user=request.user).order_by('-timestamp')[:50]

    log_access(
        request.user,
        'data_view',
        'Viewed access logs',
        request
    )

    context = {
        'access_logs': logs
    }

    return render(request, 'settings.html', context)


@login_required
@require_http_methods(["POST"])
def request_data_export(request):
    """Request data export"""

    # Check if there's already a pending request
    existing_request = DataExportRequest.objects.filter(
        user=request.user,
        status__in=['pending', 'processing']
    ).exists()

    if existing_request:
        messages.warning(request, 'You already have a pending data export request.')
        return redirect('settings')

    # Create export request
    export_request = DataExportRequest.objects.create(
        user=request.user,
        status='processing',
        expires_at=timezone.now() + timedelta(days=7)
    )

    log_access(
        request.user,
        'data_download',
        'Requested data export',
        request
    )

    # In a real application, you would trigger an async task here
    export_user_data(request.user)

    messages.success(request, 'Data export request received. You will receive an email shortly.')
    return redirect('settings')


def export_user_data(user):
    """Generate and store user data export"""
    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(['Personal Information'])
    writer.writerow(['Field', 'Value'])
    writer.writerow(['Username', user.username])
    writer.writerow(['Email', user.email])
    writer.writerow(['First Name', user.first_name])
    writer.writerow(['Last Name', user.last_name])
    writer.writerow(['Joined Date', user.date_joined])

    writer.writerow([])
    writer.writerow(['Account Information'])
    writer.writerow(['Field', 'Value'])

    try:
        profile = user.profile
        writer.writerow(['User Type', profile.get_user_type_display()])
        writer.writerow(['Profession', profile.get_profession_display()])
    except UserProfile.DoesNotExist:
        pass

    writer.writerow([])
    writer.writerow(['Access Logs'])
    writer.writerow(['Timestamp', 'Type', 'IP Address', 'Description'])

    for log in AccessLog.objects.filter(user=user).order_by('-timestamp')[:100]:
        writer.writerow([
            log.timestamp,
            log.get_access_type_display(),
            log.ip_address,
            log.description
        ])

    # Update export request
    try:
        export_req = DataExportRequest.objects.get(user=user, status='processing')
        export_req.status = 'completed'
        export_req.completed_at = timezone.now()
        export_req.save()
    except DataExportRequest.DoesNotExist:
        pass


@login_required
@require_http_methods(["GET", "POST"])
def request_account_deletion(request):
    """Request account deletion"""
    if request.method == 'POST':
        reason = request.POST.get('reason', '')

        # Check if there's already a pending deletion request
        existing_request = DeleteAccountRequest.objects.filter(
            user=request.user,
            status__in=['pending', 'confirmed']
        ).exists()

        if existing_request:
            messages.warning(request, 'You already have a pending account deletion request.')
            return redirect('settings')

        # Create deletion request
        delete_request = DeleteAccountRequest.objects.create(
            user=request.user,
            reason=reason,
            status='pending'
        )

        log_access(
            request.user,
            'data_update',
            'Requested account deletion',
            request
        )

        messages.success(
            request,
            'Account deletion request received. Please check your email to confirm.'
        )

        return redirect('settings')

    return render(request, 'settings.html')


@login_required
@require_http_methods(["POST"])
def confirm_account_deletion(request, token=None):
    """Confirm account deletion"""
    try:
        delete_request = DeleteAccountRequest.objects.get(
            user=request.user,
            status='pending'
        )

        delete_request.status = 'confirmed'
        delete_request.confirmed_at = timezone.now()
        delete_request.scheduled_deletion_date = timezone.now() + timedelta(days=30)
        delete_request.save()

        log_access(
            request.user,
            'data_update',
            'Confirmed account deletion (scheduled for 30 days)',
            request
        )

        messages.success(
            request,
            'Account deletion confirmed. Your account will be permanently deleted in 30 days.'
        )

        return redirect('logout')

    except DeleteAccountRequest.DoesNotExist:
        messages.error(request, 'No pending deletion request found.')
        return redirect('settings')


@login_required
@require_http_methods(["POST"])
def cancel_account_deletion(request):
    """Cancel pending account deletion"""
    try:
        delete_request = DeleteAccountRequest.objects.get(
            user=request.user,
            status='confirmed'
        )

        delete_request.status = 'cancelled'
        delete_request.save()

        log_access(
            request.user,
            'data_update',
            'Cancelled account deletion',
            request
        )

        messages.success(request, 'Account deletion has been cancelled.')
        return redirect('settings')

    except DeleteAccountRequest.DoesNotExist:
        messages.error(request, 'No pending deletion request found.')
        return redirect('settings')


@login_required
def download_user_data(request):
    """Download user data as CSV file"""
    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(['Personal Information'])
    writer.writerow(['Field', 'Value'])
    writer.writerow(['Username', request.user.username])
    writer.writerow(['Email', request.user.email])
    writer.writerow(['First Name', request.user.first_name])
    writer.writerow(['Last Name', request.user.last_name])
    writer.writerow(['Joined Date', request.user.date_joined])

    writer.writerow([])
    writer.writerow(['Access Logs (Last 100)'])
    writer.writerow(['Timestamp', 'Type', 'IP Address', 'Description'])

    for log in AccessLog.objects.filter(user=request.user).order_by('-timestamp')[:100]:
        writer.writerow([
            log.timestamp,
            log.get_access_type_display(),
            log.ip_address,
            log.description
        ])

    # Create response
    response = FileResponse(BytesIO(output.getvalue().encode()))
    response['Content-Type'] = 'text/csv'
    response['Content-Disposition'] = f'attachment; filename="user_data_{request.user.username}.csv"'

    log_access(
        request.user,
        'data_download',
        'Downloaded personal data',
        request
    )

    return response

def user_login(request):
    """Handle user login"""
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

                # Log the login
                log_access(user, 'login', 'User logged in', request)

                if not request.POST.get("remember_me"):
                    request.session.set_expiry(0)
                else:
                    request.session.set_expiry(1209600)

                return redirect("homepage")
            else:
                messages.error(request, "Incorrect password.")
                # Log failed login
                if 'user_obj' in locals():
                    log_access(user_obj, 'failed_login', 'Failed login attempt', request)
    else:
        form = LoginForm()

    return render(request, "login.html", {"form": form})


def signup(request):
    print("🟢 signup view triggered!")

    if request.method == "POST":
        print(f"➡️ Received request method: {request.method}")
        print(f"📦 Raw POST data: {request.POST}")

        form = SignupForm(request.POST)
        print("🧩 SignupForm instance created")

        if form.is_valid():
            print("✅ Form is valid!")

            try:
                user = form.save()
                print(f"👤 User '{user.username}' created successfully")

                # Log the signup
                log_access(user, 'login', 'New account created', request)
                print("🪵 Signup logged")

                messages.success(request, f"Account created for {user.username}. You can now login.")
                print("✅ Redirecting to login...")
                return redirect("user_login")

            except Exception as e:
                print(f"❌ Exception during user creation: {e}")
                try:
                    user.delete()
                except Exception as e2:
                    print(f"⚠️ Failed to delete user after error: {e2}")

                messages.error(request, f"Error creating account: {str(e)}")
                return render(request, "signup.html", {"form": form})
        else:
            print("❌ Form is invalid!")
            print("Errors:", form.errors)
    else:
        form = SignupForm()
        print("🔵 GET request — rendering signup form")

    return render(request, "signup.html", {"form": form})



@login_required
def homepage(request):
    """Display user homepage"""

    # Log homepage visit
    log_access(request.user, 'data_view', 'Viewed homepage', request)

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
    """Handle appointment booking"""
    if request.method == "POST":
        patient = request.user
        doctor = request.POST.get("doctor")
        date = request.POST.get("date")
        time = request.POST.get("time")

        # Log appointment booking
        log_access(
            request.user,
            'data_update',
            f'Booked appointment with {doctor} on {date}',
            request
        )

        messages.success(request, "Appointment booked successfully!")
        return redirect("upcoming_appointments")

    return render(request, "book_appointment.html")


@login_required
def upcoming_appointments(request):
    """Display user's upcoming appointments"""

    log_access(request.user, 'data_view', 'Viewed upcoming appointments', request)

    # Example: Fetch appointments from DB
    # appointments = Appointment.objects.filter(patient=request.user)
    appointments = [
        {"doctor": "Dr. Banyo", "date": "2025-10-05", "time": "10:00 AM"},
        {"doctor": "Dr. Hernandez", "date": "2025-10-07", "time": "2:30 PM"},
    ]
    return render(request, "upcoming_appointments.html", {"appointments": appointments})


@login_required
def request_prescription(request):
    """Handle prescription refill requests"""
    if request.method == "POST":
        medication = request.POST.get("medication")
        notes = request.POST.get("notes")

        log_access(
            request.user,
            'data_update',
            f'Requested prescription refill for {medication}',
            request
        )

        messages.success(request, "Prescription refill request submitted!")
        return redirect("homepage")

    return render(request, "request_prescription.html")