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
from functools import wraps

from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm, CustomPasswordChangeForm, NotificationPreferencesForm
from .models import (
    UserProfile, NotificationPreference, AccessLog,
    DataExportRequest, DeleteAccountRequest, PatientAppointment
)


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
                log_access(user, 'login', 'User logged in', request)

                if not request.POST.get("remember_me"):
                    request.session.set_expiry(0)
                else:
                    request.session.set_expiry(1209600)

                # Redirect based on role
                try:
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
            # Create user with temporary password
            temp_password = str(123456)
            user = User.objects.create_user(
                username=username,
                email=email,
                password=temp_password,
                first_name=first_name,
                last_name=last_name
            )

            # Create profile with role
            profile = UserProfile.objects.create(
                user=user,
                role=role,
                department=department,
                license_number=license_number
            )

            # Create notification preferences
            NotificationPreference.objects.create(user=user)

            log_access(
                request.user,
                'data_update',
                f'Created new {role} account: {username}',
                request
            )

            messages.success(
                request,
                f'{role.title()} account created for {username}. Temporary password: {temp_password}'
            )
            return redirect('manage_staff')

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
@require_http_methods(["POST"])
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