from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.cache import never_cache
from .forms import PatientRecordForm, VisitLogForm
from .models import PatientRecord
from django.db.models import Q

def is_doctor_or_admin(user):
    return user.is_authenticated and hasattr(user, 'profile') and user.profile.role in ['doctor', 'admin']

@never_cache
@login_required
@user_passes_test(is_doctor_or_admin)
def create_patient_record(request):
    if request.method == 'POST':
        form = PatientRecordForm(request.POST, request.FILES)
        if form.is_valid():
            record = form.save(commit=False)
            
            # If the user is a doctor and the physician hasn't been explicitly selected (or is empty), assign the current user
            if hasattr(request.user, 'profile') and request.user.profile.role == 'doctor' and not record.attending_physician:
                 record.attending_physician = request.user
                 
            record.save()
            return redirect('patient_record_detail', pk=record.pk)
        else:
            return render(request, 'records/create_patient.html', {'form': form})
    else:
        initial_data = {}
        # Set the current doctor as the default attending physician on the form
        if hasattr(request.user, 'profile') and request.user.profile.role == 'doctor':
            initial_data['attending_physician'] = request.user
            
        form = PatientRecordForm(initial=initial_data)
        return render(request, 'records/create_patient.html', {'form': form})

@login_required
@user_passes_test(is_doctor_or_admin)
def update_patient_record(request, pk):
    record = get_object_or_404(PatientRecord, pk=pk) 
    
    if request.method == 'POST':
        form = PatientRecordForm(request.POST, request.FILES, instance=record)
        if form.is_valid():
            # If the user is a doctor, ensure they are either the attending physician or an admin to save
            if request.user.profile.role == 'doctor' and request.user != record.attending_physician:
                # Optionally add a message here: messages.error(request, "Permission denied.")
                return redirect('patient_record_detail', pk=record.pk) 
                
            form.save()
            return redirect('patient_record_detail', pk=record.pk)
    else:
        form = PatientRecordForm(instance=record) 

    context = {
        'form': form,
        'record': record,
    }
    # Reuses the create_patient.html template for editing
    return render(request, 'records/create_patient.html', context) 

@login_required
@user_passes_test(is_doctor_or_admin)
def patient_record_detail(request, pk):
    record = get_object_or_404(PatientRecord, pk=pk)
    
    context = {
        'record': record,
    }
    return render(request, 'records/patient_record_detail.html', context)

@login_required
@user_passes_test(is_doctor_or_admin)
def records_list(request):
    # Base queryset for all records
    queryset = PatientRecord.objects.all().select_related('attending_physician').order_by('-created_at')
    
    # Optional: Filter for doctors to only see their patients (Admin sees all)
    if request.user.profile.role == 'doctor':
        queryset = queryset.filter(attending_physician=request.user)
    
    context = {
        'records': queryset,
    }
    return render(request, 'records/records_list.html', context)


@login_required
@user_passes_test(is_doctor_or_admin)
def add_visit_log(request, pk):
    patient = get_object_or_404(PatientRecord, pk=pk) 
    
    if request.method == 'POST':
        # Ensure you have imported and defined VisitLogForm in forms.py
        log_form = VisitLogForm(request.POST) 
        if log_form.is_valid():
            visit_log = log_form.save(commit=False)
            visit_log.patient = patient
            visit_log.clinician = request.user
            visit_log.save()
            
            return redirect('patient_record_detail', pk=patient.pk)
    else:
        log_form = VisitLogForm() 

    context = {
        'patient': patient,
        'log_form': log_form,
        'recent_logs': patient.visit_history.all()[:3],
    }
    # This template will likely be 'records/add_visit_log.html'
    return render(request, 'records/add_visit_log.html', context)