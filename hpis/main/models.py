from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    """Extended user profile with role-based access"""

    ROLE_CHOICES = (
        ('super_admin', 'Super Admin'),
        ('admin', 'Admin'),
        ('doctor', 'Doctor'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='doctor', db_index=True)
    department = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    license_number = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    must_change_password = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
        indexes = [
            models.Index(fields=['role', 'department']),
        ]


class PatientAppointment(models.Model):
    """Store patient appointment requests"""

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('assigned', 'Assigned to Doctor'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    APPOINTMENT_TYPE_CHOICES = (
        ('consultation', 'General Consultation'),
        ('followup', 'Follow-up'),
        ('checkup', 'Routine Checkup'),
        ('emergency', 'Emergency'),
    )

    # Patient Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')])
    email = models.EmailField()
    contact_number = models.CharField(max_length=20)
    address = models.TextField()

    # Appointment Details
    appointment_type = models.CharField(max_length=20, choices=APPOINTMENT_TYPE_CHOICES, db_index=True)
    appointment_date = models.DateField(db_index=True)
    appointment_time = models.TimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    # Status & Assignment
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    assigned_doctor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_appointments', db_index=True)
    assigned_admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_appointments')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.appointment_date}"

    class Meta:
        verbose_name = "Patient Appointment"
        verbose_name_plural = "Patient Appointments"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'appointment_date']),
            models.Index(fields=['assigned_doctor', 'status']),
            models.Index(fields=['-created_at']),
        ]


class NotificationPreference(models.Model):
    """Store user notification preferences"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preference')
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=True)
    prescription_alerts = models.BooleanField(default=True)
    system_updates = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Notification Preferences for {self.user.username}"

    class Meta:
        verbose_name = "Notification Preference"
        verbose_name_plural = "Notification Preferences"


class AccessLog(models.Model):
    """Track access to user accounts and data"""

    ACCESS_TYPE_CHOICES = (
        ('login', 'Login'),
        ('data_view', 'Data View'),
        ('data_update', 'Data Update'),
        ('logout', 'Logout'),
        ('failed_login', 'Failed Login'),
        ('data_download', 'Data Download'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='access_logs', db_index=True)
    access_type = models.CharField(max_length=20, choices=ACCESS_TYPE_CHOICES, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_access_type_display()} at {self.timestamp}"

    class Meta:
        verbose_name = "Access Log"
        verbose_name_plural = "Access Logs"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['access_type', '-timestamp']),
        ]


class DataExportRequest(models.Model):
    """Track user data export requests"""

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='data_export_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    download_url = models.URLField(blank=True, null=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Data Export for {self.user.username} - {self.get_status_display()}"

    class Meta:
        verbose_name = "Data Export Request"
        verbose_name_plural = "Data Export Requests"
        ordering = ['-requested_at']


class DeleteAccountRequest(models.Model):
    """Track account deletion requests"""

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('deleted', 'Deleted'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delete_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reason = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    scheduled_deletion_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Delete Request for {self.user.username} - {self.get_status_display()}"

    class Meta:
        verbose_name = "Delete Account Request"
        verbose_name_plural = "Delete Account Requests"
        ordering = ['-requested_at']


# Add to the end of models.py
class Report(models.Model):
    """Store generated reports"""

    REPORT_TYPE_CHOICES = (
        ('patient_records', 'Patient Records'),
        ('appointments', 'Appointments'),
        ('analytics', 'System Analytics'),
        ('audit', 'Audit Trail'),
    )

    FORMAT_CHOICES = (
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    report_type = models.CharField(max_length=50, choices=REPORT_TYPE_CHOICES)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Filters
    date_from = models.DateField(null=True, blank=True)
    date_to = models.DateField(null=True, blank=True)

    # File info
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Report'
        verbose_name_plural = 'Reports'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_report_type_display()} - {self.user.username}"