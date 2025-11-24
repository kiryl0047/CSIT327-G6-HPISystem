# records/models.py

from django.db import models
from django.conf import settings
from datetime import date
from django.contrib.auth.models import User

class PatientRecord(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    full_name = models.CharField(max_length=255)
    date_of_birth = models.DateField(null=True, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    department = models.CharField(max_length=50)
    attending_physician = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    photo = models.ImageField(upload_to='patient_photos/', null=True, blank=True)

    patient_code = models.CharField(max_length=20, unique=True, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Auto-calculate age
        if self.date_of_birth:
            today = date.today()
            self.age = today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        else:
            self.age = None

        # Auto-generate patient_code if not set
        if not self.patient_code:
            year = date.today().year
            # Get next sequence number
            last_record = PatientRecord.objects.filter(created_at__year=year).order_by('id').last()
            next_number = 1 if not last_record else last_record.id + 1
            self.patient_code = f"PAT-{year}-{str(next_number).zfill(3)}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.patient_code} - {self.full_name}"


class VisitLog(models.Model):
    patient = models.ForeignKey(
        PatientRecord,
        on_delete=models.CASCADE,
        related_name='visit_history'
    )
    clinician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='log_entries'
    )
    visit_date = models.DateTimeField(auto_now_add=True)

    diagnosis = models.TextField(blank=True, null=True)
    vitals = models.TextField(blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    medications = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-visit_date']

    def __str__(self):
        return f"Visit Log for {self.patient.full_name} on {self.visit_date.strftime('%Y-%m-%d')}"