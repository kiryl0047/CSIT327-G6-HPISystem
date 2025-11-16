from django.db import models
from django.conf import settings
from datetime import date

class PatientRecord(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    full_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    department = models.CharField(max_length=100)
    
    attending_physician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'profile__role': 'doctor'}
    )
    photo = models.ImageField(upload_to='patient_photos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    def save(self, *args, **kwargs):
        if self.date_of_birth:
            today = date.today()
            self.age = today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        else:
            self.age = None
            
        super().save(*args, **kwargs)

    def __str__(self):
        return self.full_name

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

    # Episodic Data
    diagnosis = models.TextField(blank=True, null=True)
    vitals = models.TextField(blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    medications = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-visit_date']

    def __str__(self):
        return f"Visit Log for {self.patient.full_name} on {self.visit_date.strftime('%Y-%m-%d')}"