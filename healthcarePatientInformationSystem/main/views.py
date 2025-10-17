from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
import string
from django.contrib import messages
from django.http import JsonResponse, FileResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from datetime import timedelta
import json
import csv
from django.contrib.auth import update_session_auth_hash
from io import BytesIO, StringIO
from functools import wraps

from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm, CustomPasswordChangeForm, NotificationPreferencesForm
from .models import (
    UserProfile, NotificationPreference, AccessLog,
    DataExportRequest, DeleteAccountRequest, PatientAppointment
)
from django.db import transaction
from django.core.mail import send_mail


# ==================== Decorators ====================

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


def role_required(*allowed_roles):
    """Decorator to check if user has required role"""

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('user_login')

            try:
                user_role = request.user.profile.role
            except UserProfile.DoesNotExist:
                return redirect('user_login')

            if user_role not in allowed_roles:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('homepage')

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


# ==================== Authentication Views ====================

def user_login(request):
    """Handle user login - Staff only"""
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data['username']
            password = form.cleaned_data['password']

            try:
                user_obj = User.objects.get(username__iexact=identifier)
            except User.DoesNotExist:
                messages.error(request, "User not found.")
                return render(request, "login.html", {"form": form})

            user = authenticate(request, username=user_obj.username, password=password)

            if user is not None:
                login(request, user)
                # If the user's profile requires a password change, redirect them to change-password
                try:
                    if user.profile.must_change_password:
                        return redirect('change_password')
                except Exception:
                    pass

                log_access(user, 'login', 'User logged in', request)

                if not request.POST.get("remember_me"):
                    request.session.set_expiry(0)
                else:
                    request.session.set_expiry(1209600)

                # Redirect based on Django flags first (superuser/staff), then profile.role
                try:
                    if user.is_superuser:
                        return redirect('super_admin_dashboard')
                    if user.is_staff:
                        return redirect('admin_dashboard')

                    role = user.profile.role
                    if role == 'super_admin':
                        return redirect('super_admin_dashboard')
                    elif role == 'admin':
                        return redirect('admin_dashboard')
                    elif role == 'doctor':
                        return redirect('doctor_dashboard')
                except UserProfile.DoesNotExist:
                    return redirect('homepage')
            else:
                messages.error(request, "Incorrect password.")
                if 'user_obj' in locals():
                    log_access(user_obj, 'failed_login', 'Failed login attempt', request)
    else:
        form = LoginForm()

    return render(request, "login.html", {"form": form})


def landing_page(request):
    """Landing page with appointment booking form for patients"""
    if request.method == "POST":
        # Create appointment from form data
        appointment = PatientAppointment.objects.create(
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            middle_name=request.POST.get('middle_name', ''),
            date_of_birth=request.POST.get('dob'),
            gender=request.POST.get('gender'),
            email=request.POST.get('email'),
            contact_number=request.POST.get('contact'),
            address=request.POST.get('address'),
            appointment_type=request.POST.get('appointment_type'),
            appointment_date=request.POST.get('available_date'),
            notes=request.POST.get('notes', ''),
            status='pending'
        )

        messages.success(
            request,
            'Your appointment request has been submitted. An admin will review and assign it to a doctor shortly.'
        )
        return render(request, 'appointment_form.html', {'appointment_submitted': True})

    return render(request, 'appointment_form.html')


# ==================== Super Admin Dashboard ====================

@login_required
@role_required('super_admin')
def super_admin_dashboard(request):
    """Super Admin main dashboard"""
    stats = {
        'total_staff': User.objects.filter(profile__role__in=['admin', 'doctor']).count(),
        'admins': User.objects.filter(profile__role='admin').count(),
        'doctors': User.objects.filter(profile__role='doctor').count(),
        'pending_appointments': PatientAppointment.objects.filter(status='pending').count(),
    }

    log_access(request.user, 'data_view', 'Accessed super admin dashboard', request)

    return render(request, 'super_admin_dashboard.html', {'stats': stats})


@login_required
@role_required('super_admin')
def create_staff(request):
    """Create new staff account (Admin or Doctor)"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        role = request.POST.get('role')
        department = request.POST.get('department', '')
        license_number = request.POST.get('license_number', '')

        # Validate role
        if role not in ['admin', 'doctor']:
            messages.error(request, 'Invalid role.')
            return redirect('create_staff')

        # Check if user exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('create_staff')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return redirect('create_staff')

        try:
            # Create user with a secure temporary password (letters+digits+punctuation)
            alphabet = string.ascii_letters + string.digits + string.punctuation
            temp_password = get_random_string(12, alphabet)
            user = User.objects.create_user(
                username=username,
                email=email,
                password=temp_password,
                first_name=first_name,
                last_name=last_name
            )

            # Create profile with role and notification preferences atomically
            # Read optional checkbox to email temp password
            email_temp = request.POST.get('email_temp_password') == 'on'

            with transaction.atomic():
                # Safely get the profile (which may have been created by a signal)
                profile, created = UserProfile.objects.get_or_create(user=user)

                # Now, update the profile's fields regardless of whether it was created now or by a signal
                profile.role = role
                profile.department = department
                profile.license_number = license_number

                # Set must_change_password flag
                profile.must_change_password = True
                
                profile.save() # <-- Save the updated fields

                # Keep the NotificationPreference check as a safety measure
                NotificationPreference.objects.get_or_create(user=user)

            # Optionally send the temporary password via email (HTML)
            if email_temp and email:
                try:
                    subject = 'Welcome to the Healthcare Patient Information System'
                    plain_message = (
                        f'Hello {first_name or username},\n\n'
                        f'An account has been created for you.\n'
                        f'Username: {username}\n'
                        f'Temporary password: {temp_password}\n\n'
                        'Please change your password on first login.\n\n'
                        'If you have any questions, contact IT Support.'
                    )

                    html_message = (
                        f'<p>Hello {first_name or username},</p>'
                        f'<p>An account has been created for you.</p>'
                        f'<ul><li><strong>Username:</strong> {username}</li>'
                        f'<li><strong>Temporary password:</strong> <code>{temp_password}</code></li></ul>'
                        f'<p>Please change your password on first login.</p>'
                        f'<p>If you have any questions, contact IT Support.</p>'
                    )

                    send_mail(
                        subject=subject,
                        message=plain_message,
                        from_email=None,
                        recipient_list=[email],
                        html_message=html_message,
                        fail_silently=True,
                    )
                except Exception:
                    # Swallow email errors but log if desired
                    pass

            log_access(
                request.user,
                'data_update',
                f'Created new {role} account: {username}',
                request
            )

            # Render a success page that shows the temporary password so admin can copy it
            return render(request, 'create_staff_success.html', {
                'username': username,
                'email': email,
                'role': role,
                'temp_password': temp_password,
                'profile': profile,
            })

        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return redirect('create_staff')

    return render(request, 'create_staff.html')


@login_required
@role_required('super_admin')
def manage_staff(request):
    """Manage all staff accounts"""
    staff = User.objects.filter(profile__role__in=['admin', 'doctor']).select_related('profile')

    log_access(request.user, 'data_view', 'Accessed manage staff page', request)

    return render(request, 'manage_staff.html', {'staff': staff})


@login_required
@role_required('super_admin')
def edit_staff(request, staff_id):
    """Edit staff account"""
    staff_user = get_object_or_404(User, id=staff_id)

    if not staff_user.profile or staff_user.profile.role not in ['admin', 'doctor']:
        messages.error(request, 'Invalid staff member.')
        return redirect('manage_staff')

    if request.method == 'POST':
        staff_user.first_name = request.POST.get('first_name')
        staff_user.last_name = request.POST.get('last_name')
        staff_user.email = request.POST.get('email')
        staff_user.save()

        staff_user.profile.role = request.POST.get('role')
        staff_user.profile.department = request.POST.get('department')
        staff_user.profile.license_number = request.POST.get('license_number')
        staff_user.profile.save()

        log_access(
            request.user,
            'data_update',
            f'Updated staff account: {staff_user.username}',
            request
        )

        messages.success(request, 'Staff account updated successfully.')
        return redirect('manage_staff')

    return render(request, 'edit_staff.html', {'staff_user': staff_user})


@login_required
@role_required('super_admin')
def delete_staff(request, staff_id):
    """Delete staff account"""
    staff_user = get_object_or_404(User, id=staff_id)

    if request.method == 'POST':
        username = staff_user.username
        staff_user.delete()

        log_access(
            request.user,
            'data_update',
            f'Deleted staff account: {username}',
            request
        )

        messages.success(request, f'Staff account {username} deleted.')
        return redirect('manage_staff')

    return render(request, 'delete_staff_confirm.html', {'staff_user': staff_user})


# ==================== Admin Dashboard ====================

@login_required
@role_required('admin')
def admin_dashboard(request):
    """Admin main dashboard"""
    pending_appointments = PatientAppointment.objects.filter(status='pending')
    assigned_appointments = PatientAppointment.objects.filter(status='assigned')
    doctors = User.objects.filter(profile__role='doctor')

    log_access(request.user, 'data_view', 'Accessed admin dashboard', request)

    context = {
        'pending_count': pending_appointments.count(),
        'assigned_count': assigned_appointments.count(),
        'pending_appointments': pending_appointments,
        'doctors': doctors,
    }

    return render(request, 'admin_dashboard.html', context)


@login_required
@role_required('admin')
def assign_appointment(request, appointment_id):
    """Assign appointment to a doctor"""
    appointment = get_object_or_404(PatientAppointment, id=appointment_id)

    if request.method == 'POST':
        doctor_id = request.POST.get('doctor_id')
        appointment_date = request.POST.get('appointment_date')
        appointment_time = request.POST.get('appointment_time')

        try:
            doctor = User.objects.get(id=doctor_id, profile__role='doctor')

            appointment.assigned_doctor = doctor
            appointment.assigned_admin = request.user
            appointment.status = 'assigned'
            appointment.appointment_date = appointment_date
            if appointment_time:
                appointment.appointment_time = appointment_time
            appointment.save()

            log_access(
                request.user,
                'data_update',
                f'Assigned appointment to Dr. {doctor.first_name}',
                request
            )

            messages.success(request, 'Appointment assigned successfully.')
            return redirect('admin_dashboard')
        except User.DoesNotExist:
            messages.error(request, 'Doctor not found.')

    return render(request, 'assign_appointment.html',
                  {'appointment': appointment, 'doctors': User.objects.filter(profile__role='doctor')})


# ==================== Doctor Dashboard ====================

@login_required
@role_required('doctor')
def doctor_dashboard(request):
    """Doctor main dashboard"""
    my_appointments = PatientAppointment.objects.filter(assigned_doctor=request.user)

    log_access(request.user, 'data_view', 'Accessed doctor dashboard', request)

    context = {
        'appointments': my_appointments,
        'confirmed_count': my_appointments.filter(status='confirmed').count(),
        'pending_count': my_appointments.filter(status='assigned').count(),
    }

    return render(request, 'doctor_dashboard.html', context)


@login_required
@role_required('doctor')
def confirm_appointment(request, appointment_id):
    """Doctor confirms appointment"""
    appointment = get_object_or_404(PatientAppointment, id=appointment_id)

    if appointment.assigned_doctor != request.user:
        messages.error(request, 'You cannot confirm this appointment.')
        return redirect('doctor_dashboard')

    if request.method == 'POST':
        appointment.status = 'confirmed'
        appointment.save()

        log_access(
            request.user,
            'data_update',
            f'Confirmed appointment for {appointment.first_name}',
            request
        )

        messages.success(request, 'Appointment confirmed.')
        return redirect('doctor_dashboard')

    return render(request, 'confirm_appointment.html', {'appointment': appointment})


# ==================== General User Views ====================

@login_required
def homepage(request):
    """User homepage - redirects based on role"""
    try:
        role = request.user.profile.role
        if role == 'super_admin':
            return redirect('super_admin_dashboard')
        elif role == 'admin':
            return redirect('admin_dashboard')
        elif role == 'doctor':
            return redirect('doctor_dashboard')
    except UserProfile.DoesNotExist:
        pass

    return redirect('user_login')


@login_required
def settings_page(request):
    """User settings page"""
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
# REMOVED: @require_http_methods(["POST"]) 
def change_password(request):
    """
    Handle password change.
    GET: Displays the form.
    POST: Processes the form submission.
    """
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)

        if form.is_valid():
            user = form.save()
            
            # 🌟 FIX: Keep the user logged in after password change 🌟
            update_session_auth_hash(request, user) 

            # Clear must_change_password flag if present...
            # ... (rest of your existing code for clearing the flag)
            try:
                profile = request.user.profile
                if profile.must_change_password:
                    profile.must_change_password = False
                    profile.save()
            except Exception:
                pass
            # ... (rest of your existing code)
            
            log_access(
                request.user,
                'data_update',
                'Changed password',
                request
            )

            messages.success(request, 'Password changed successfully! You are still logged in.')
            return redirect('settings')

    else: # Handles the GET request, including the redirect from user_login
        form = CustomPasswordChangeForm(request.user)
    
    # Renders the change password form, likely integrated into settings.html
    # Note: If your change_password URL is meant to be a standalone page, 
    #       you might need a separate template, but based on your structure, 
    #       it seems to be a dedicated endpoint that renders the form within settings.
    # We will redirect to settings instead, as the form should live there.
    
    # If the user is on the change_password URL directly via GET, we redirect them 
    # to the main settings page which will render the form using the settings_page view.
    return redirect('settings')

# The settings_page view needs to be updated to pass the form object for the template.
# But for now, fixing the redirect logic in user_login is the most direct solution 
# combined with removing the POST-only decorator.


@login_required
@require_http_methods(["POST"])
def update_notifications(request):
    """Handle notification preference updates"""
    try:
        notification_pref = request.user.notification_preference
    except NotificationPreference.DoesNotExist:
        notification_pref = NotificationPreference.objects.create(user=request.user)

    if request.method == 'POST':
        notification_pref.email_notifications = request.POST.get('email_notifications') == 'on'
        notification_pref.sms_notifications = request.POST.get('sms_notifications') == 'on'
        notification_pref.prescription_alerts = request.POST.get('prescription_alerts') == 'on'
        notification_pref.system_updates = request.POST.get('system_updates') == 'on'
        notification_pref.save()

        log_access(
            request.user,
            'data_update',
            'Updated notification preferences',
            request
        )

        messages.success(request, 'Notification preferences updated successfully!')
        return redirect('settings')

    return JsonResponse({'status': 'error'}, status=400)