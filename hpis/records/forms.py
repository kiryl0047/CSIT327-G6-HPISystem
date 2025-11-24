# records/forms.py

from django import forms
from django.contrib.auth.models import User
from .models import PatientRecord, VisitLog
from main.models import UserProfile

DEPARTMENT_CHOICES = [
    ('general_medicine', 'General Medicine'),
    ('pediatrics', 'Pediatrics'),
    ('cardiology', 'Cardiology'),
    ('dermatology', 'Dermatology'),
    ('neurology', 'Neurology'),
    ('orthopedics', 'Orthopedics'),
    ('obgyn', 'OB-GYN'),
    ('psychiatry', 'Psychiatry'),
    ('surgery', 'Surgery'),
]


class PatientRecordForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        label='Date of Birth',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=True
    )

    def __init__(self, *args, **kwargs):
        super(PatientRecordForm, self).__init__(*args, **kwargs)
        # Restrict physician choices to doctors only
        if 'attending_physician' in self.fields:
            self.fields['attending_physician'].queryset = User.objects.filter(profile__role='doctor')

    class Meta:
        model = PatientRecord
        fields = [
            'full_name', 'date_of_birth', 'age', 'gender', 'department',
            'attending_physician', 'photo'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter full name'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly', 'placeholder': 'Auto-calculated'}),
            'gender': forms.Select(attrs={'class': 'form-control'}, choices=PatientRecord.GENDER_CHOICES),
            'department': forms.Select(attrs={'class': 'form-control'}, choices=DEPARTMENT_CHOICES),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'attending_physician': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        full_name = cleaned_data.get('full_name')
        date_of_birth = cleaned_data.get('date_of_birth')

        if full_name and date_of_birth:
            if PatientRecord.objects.filter(full_name=full_name, date_of_birth=date_of_birth).exists():
                existing = PatientRecord.objects.get(full_name=full_name, date_of_birth=date_of_birth)
                raise forms.ValidationError(
                    f"Patient {full_name} already exists. "
                    f"<a href='/records/{existing.pk}/'>Jump to Record</a>"
                )
        return cleaned_data


class VisitLogForm(forms.ModelForm):
    class Meta:
        model = VisitLog
        fields = ['diagnosis', 'vitals', 'allergies', 'medications']
        widgets = {
            'diagnosis': forms.Textarea(attrs={'class': 'form-control textarea-lg', 'placeholder': 'New/Updated Diagnosis'}),
            'vitals': forms.Textarea(attrs={'class': 'form-control textarea-md', 'placeholder': 'Current Vitals (BP, HR, Temp, etc.)'}),
            'allergies': forms.Textarea(attrs={'class': 'form-control textarea-md', 'placeholder': 'List known allergies (updated)'}),
            'medications': forms.Textarea(attrs={'class': 'form-control textarea-md', 'placeholder': 'Current medications (updated)'}),
        }