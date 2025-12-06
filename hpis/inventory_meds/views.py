from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, F, Sum, Count
from django.utils import timezone
from django.http import HttpResponseForbidden, JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db import transaction
import csv
from datetime import timedelta

from .models import Medicine, StockMovement, DispenseRecord, Supplier, MedicineAuditLog
from .forms import (
    MedicineForm, MedicineEditForm, StockAdjustmentForm, 
    DispenseForm, SupplierForm, SearchFilterForm
)


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_audit(medicine, action, user, field_name='', old_value='', new_value='', reason='', patient=None, request=None):
    """Create audit log entry"""
    MedicineAuditLog.objects.create(
        medicine=medicine,
        action=action,
        user=user,
        field_name=field_name,
        old_value=str(old_value),
        new_value=str(new_value),
        reason=reason,
        patient=patient,
        ip_address=get_client_ip(request) if request else None
    )


def check_permission(user, required_roles):
    """Check if user has required role"""
    if not hasattr(user, 'userprofile'):
        return False
    return user.userprofile.role in required_roles


@login_required
def inventory_dashboard(request):
    """Main inventory dashboard with summary, alerts, and medicine list"""
    
    # Get all medicines (as a QuerySet)
    medicines = Medicine.objects.select_related('supplier').all()
    
    # Apply filters
    form = SearchFilterForm(request.GET or None)
    if form.is_valid():
        search = form.cleaned_data.get('search')
        if search:
            medicines = medicines.filter(
                Q(name__icontains=search) |
                Q(brand_name__icontains=search) |
                Q(category__icontains=search) |
                Q(batch_number__icontains=search) |
                Q(manufacturer__icontains=search)
            )        
        
        category = form.cleaned_data.get('category')
        if category:
            medicines = medicines.filter(category=category)
            
        status = form.cleaned_data.get('status')
        if status:
            medicines = medicines.filter(status=status)
        
        stock_filter = form.cleaned_data.get('stock_filter')
        if stock_filter == 'low':
            # FIX: Use QuerySet filter instead of list comprehension
            medicines = medicines.filter(
                quantity_on_hand__lte=F('reorder_level'),
                quantity_on_hand__gt=0
            )
        elif stock_filter == 'out':
            medicines = medicines.filter(quantity_on_hand=0)
        elif stock_filter == 'adequate':
            medicines = medicines.filter(quantity_on_hand__gt=F('reorder_level'))
        
        expiry_filter = form.cleaned_data.get('expiry_filter')
        # Define the timedelta once
        thirty_days_ahead = timezone.now().date() + timedelta(days=30)
        
        if expiry_filter == 'expiring_soon':
            medicines = medicines.filter(
                expires_on__lte=thirty_days_ahead,
                expires_on__gt=timezone.now().date()
            )
        elif expiry_filter == 'expired':
            medicines = medicines.filter(expires_on__lte=timezone.now().date())
        
        prescription_only = form.cleaned_data.get('prescription_only')
        if prescription_only == 'yes':
            medicines = medicines.filter(prescription_only=True)
        elif prescription_only == 'no':
            medicines = medicines.filter(prescription_only=False)
    
    # Calculate summary statistics (FIX: Use efficient database counts)
    total_items = Medicine.objects.count()
    
    low_stock_count = Medicine.objects.filter(
        quantity_on_hand__lte=F('reorder_level'), 
        quantity_on_hand__gt=0
    ).count()
    
    out_of_stock_count = Medicine.objects.filter(quantity_on_hand=0).count()
    
    # Use the same time calculation as the filter
    thirty_days_ahead = timezone.now().date() + timedelta(days=30)
    expiring_soon_count = Medicine.objects.filter(
        expires_on__lte=thirty_days_ahead,
        expires_on__gt=timezone.now().date()
    ).count()
    
    expired_count = Medicine.objects.filter(
        expires_on__lte=timezone.now().date()
    ).count()
    
    # Pagination
    paginator = Paginator(medicines, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get role-based permissions - TEMPORARY: Allow all users full access
    user_role = request.user.userprofile.role if hasattr(request.user, 'userprofile') else None
    can_add = True  # Temporarily allow all users
    can_edit = True  # Temporarily allow all users
    can_delete = True  # Temporarily allow all users
    can_dispense = True  # Temporarily allow all users
    
    context = {
        "title": "Medicine Inventory Dashboard",
        "medicines": page_obj,
        "form": form,
        "total_items": total_items,
        "low_stock_count": low_stock_count,
        "out_of_stock_count": out_of_stock_count,
        "expiring_soon_count": expiring_soon_count,
        "expired_count": expired_count,
        "user_role": user_role,
        "can_add": can_add,
        "can_edit": can_edit,
        "can_delete": can_delete,
        "can_dispense": can_dispense,
    }
    return render(request, "inventory_meds/dashboard.html", context)

@login_required
def add_medicine(request):
    """Add new medicine entry"""
    
    # TEMPORARY: Remove permission check to allow all users
    # if not check_permission(request.user, ['Admin', 'Nurse', 'Pharmacist']):
    #     log_audit(None, MedicineAuditLog.ACTION_ACCESS_DENIED, request.user.userprofile,
    #              reason="Attempted to add medicine", request=request)
    #     messages.error(request, "You do not have permission to add medicines.")
    #     return HttpResponseForbidden("Access denied: insufficient privileges.")
    
    if request.method == 'POST':
        form = MedicineForm(request.POST)
        if form.is_valid():
            try:
                medicine = form.save()
                log_audit(medicine, MedicineAuditLog.ACTION_CREATE, request.user.userprofile,
                         reason="New medicine added", request=request)
                messages.success(request, f"Medicine '{medicine.name}' added successfully!")
                return redirect('inventory_meds:dashboard')
            except Exception as e:
                messages.error(request, f"Failed to add medicine: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = MedicineForm()
    
    context = {
        "title": "Add New Medicine",
        "form": form,
    }
    return render(request, "inventory_meds/add_medicine.html", context)


@login_required
def edit_medicine(request, medicine_id):
    """Edit existing medicine"""
    
    medicine = get_object_or_404(Medicine, pk=medicine_id)
    
    # TEMPORARY: Remove permission check to allow all users
    # if not check_permission(request.user, ['Admin', 'Nurse', 'Pharmacist']):
    #     log_audit(medicine, MedicineAuditLog.ACTION_ACCESS_DENIED, request.user.userprofile,
    #              reason="Attempted to edit medicine", request=request)
    #     messages.error(request, "You do not have permission to edit medicines.")
    #     return HttpResponseForbidden("Access denied: insufficient privileges.")
    
    if request.method == 'POST':
        form = MedicineEditForm(request.POST, instance=medicine)
        if form.is_valid():
            try:
                # Track changes
                changed_fields = form.changed_data
                old_values = {field: getattr(medicine, field) for field in changed_fields}
                
                updated_medicine = form.save()
                
                # Log each changed field
                for field in changed_fields:
                    log_audit(
                        updated_medicine, 
                        MedicineAuditLog.ACTION_UPDATE, 
                        request.user.userprofile,
                        field_name=field,
                        old_value=old_values[field],
                        new_value=getattr(updated_medicine, field),
                        request=request
                    )
                
                messages.success(request, f"Medicine '{medicine.name}' updated successfully!")
                return redirect('inventory_meds:view_medicine', medicine_id=medicine.id)
            except Exception as e:
                messages.error(request, f"Failed to update medicine: {str(e)}")
    else:
        form = MedicineEditForm(instance=medicine)
    
    context = {
        "title": f"Edit Medicine: {medicine.name}",
        "form": form,
        "medicine": medicine,
    }
    return render(request, "inventory_meds/edit_medicine.html", context)


@login_required
def view_medicine(request, medicine_id):
    """View medicine details"""
    
    medicine = get_object_or_404(Medicine.objects.select_related('supplier'), pk=medicine_id)
    
    # Get recent movements
    recent_movements = medicine.movements.select_related('performed_by')[:10]
    
    # Get recent dispenses
    recent_dispenses = medicine.dispenses.select_related('patient', 'dispensed_by')[:10]
    
    # Get audit logs
    audit_logs = medicine.audit_logs.select_related('user')[:20]
    
    # Check permissions
    # TEMPORARY: Allow all users full access
    can_edit = True
    can_adjust_stock = True
    can_dispense = True
    
    context = {
        "title": f"Medicine: {medicine.name}",
        "medicine": medicine,
        "recent_movements": recent_movements,
        "recent_dispenses": recent_dispenses,
        "audit_logs": audit_logs,
        "can_edit": can_edit,
        "can_adjust_stock": can_adjust_stock,
        "can_dispense": can_dispense,
    }
    return render(request, "inventory_meds/view_medicine.html", context)


@login_required
def archive_medicine(request, medicine_id):
    """Archive (soft delete) a medicine"""
    
    medicine = get_object_or_404(Medicine, pk=medicine_id)
    
    # TEMPORARY: Remove permission check to allow all users
    # if not check_permission(request.user, ['Admin']):
    #     log_audit(medicine, MedicineAuditLog.ACTION_ACCESS_DENIED, request.user.userprofile,
    #              reason="Attempted to archive medicine", request=request)
    #     messages.error(request, "You are not authorized to archive medicines.")
    #     return HttpResponseForbidden("Access denied: insufficient privileges.")
    
    if request.method == 'POST':
        try:
            old_status = medicine.status
            medicine.status = Medicine.STATUS_DISCONTINUED
            medicine.save()
            
            log_audit(medicine, MedicineAuditLog.ACTION_ARCHIVE, request.user.userprofile,
                     field_name='status', old_value=old_status, 
                     new_value=Medicine.STATUS_DISCONTINUED, request=request)
            
            messages.success(request, f"Medicine '{medicine.name}' has been archived.")
            return redirect('inventory_meds:dashboard')
        except Exception as e:
            messages.error(request, f"Failed to archive medicine: {str(e)}")
    
    context = {
        "title": "Archive Medicine",
        "medicine": medicine,
    }
    return render(request, "inventory_meds/confirm_archive.html", context)


@login_required
def adjust_stock(request, medicine_id):
    """Adjust medicine stock"""
    
    medicine = get_object_or_404(Medicine, pk=medicine_id)
    
    # TEMPORARY: Remove permission check to allow all users
    # if not check_permission(request.user, ['Admin', 'Nurse', 'Pharmacist']):
    #     log_audit(medicine, MedicineAuditLog.ACTION_ACCESS_DENIED, request.user.userprofile,
    #              reason="Attempted to adjust stock", request=request)
    #     messages.error(request, "You do not have permission to modify stock.")
    #     return HttpResponseForbidden("Access denied: insufficient privileges.")
    
    if request.method == 'POST':
        form = StockAdjustmentForm(request.POST, medicine=medicine)
        if form.is_valid():
            try:
                with transaction.atomic():
                    adjustment_type = form.cleaned_data['adjustment_type']
                    quantity = form.cleaned_data['quantity']
                    reason = form.cleaned_data['reason']
                    batch_number = form.cleaned_data.get('batch_number', '')
                    
                    old_quantity = medicine.quantity_on_hand
                    
                    if adjustment_type == 'add':
                        medicine.quantity_on_hand += quantity
                        movement_type = StockMovement.MOVEMENT_IN
                        action = MedicineAuditLog.ACTION_STOCK_ADD
                    else:
                        medicine.quantity_on_hand -= quantity
                        movement_type = StockMovement.MOVEMENT_OUT
                        action = MedicineAuditLog.ACTION_STOCK_REDUCE
                    
                    medicine.save()
                    
                    # Create stock movement record
                    StockMovement.objects.create(
                        medicine=medicine,
                        movement_type=movement_type,
                        quantity=quantity if adjustment_type == 'add' else -quantity,
                        reason=reason,
                        reference=batch_number,
                        performed_by=request.user.userprofile
                    )
                    
                    # Log audit
                    log_audit(
                        medicine, action, request.user.userprofile,
                        field_name='quantity_on_hand',
                        old_value=old_quantity,
                        new_value=medicine.quantity_on_hand,
                        reason=reason,
                        request=request
                    )
                    
                    messages.success(request, f"Stock adjusted successfully for '{medicine.name}'!")
                    return redirect('inventory_meds:view_medicine', medicine_id=medicine.id)
            except Exception as e:
                messages.error(request, f"Stock update failed. No changes were saved. Error: {str(e)}")
    else:
        form = StockAdjustmentForm(medicine=medicine)
    
    context = {
        "title": f"Adjust Stock: {medicine.name}",
        "form": form,
        "medicine": medicine,
    }
    return render(request, "inventory_meds/adjust_stock.html", context)


@login_required
def dispense_medicine(request, medicine_id=None):
    """Dispense medicine to patient"""
    
    # TEMPORARY: Remove permission check to allow all users
    # if not check_permission(request.user, ['Admin', 'Doctor', 'Nurse', 'Pharmacist']):
    #     log_audit(None, MedicineAuditLog.ACTION_ACCESS_DENIED, request.user.userprofile,
    #              reason="Attempted to dispense medicine", request=request)
    #     messages.error(request, "You do not have permission to dispense medicines.")
    #     return HttpResponseForbidden("Access denied: insufficient privileges.")
    
    medicine = None
    if medicine_id:
        medicine = get_object_or_404(Medicine, pk=medicine_id)
    
    if request.method == 'POST':
        form = DispenseForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    dispense = form.save(commit=False)
                    dispense.dispensed_by = request.user.userprofile
                    
                    # Record stock before and after
                    dispense.stock_before = dispense.medicine.quantity_on_hand
                    dispense.medicine.quantity_on_hand -= dispense.quantity
                    dispense.stock_after = dispense.medicine.quantity_on_hand
                    dispense.batch_number = dispense.medicine.batch_number
                    
                    dispense.medicine.save()
                    dispense.save()
                    
                    # Create stock movement
                    StockMovement.objects.create(
                        medicine=dispense.medicine,
                        movement_type=StockMovement.MOVEMENT_OUT,
                        quantity=-dispense.quantity,
                        reason=f"Dispensed to patient: {dispense.patient.full_name}",
                        reference=f"DISP-{dispense.id}",
                        performed_by=request.user.userprofile
                    )
                    
                    # Log audit
                    log_audit(
                        dispense.medicine, 
                        MedicineAuditLog.ACTION_DISPENSE, 
                        request.user.userprofile,
                        reason=f"Dispensed {dispense.quantity} to {dispense.patient.full_name}",
                        patient=dispense.patient,
                        request=request
                    )
                    
                    messages.success(request, 
                        f"Successfully dispensed {dispense.quantity} {dispense.medicine.name} to {dispense.patient.full_name}")
                    return redirect('inventory_meds:dashboard')
            except Exception as e:
                messages.error(request, f"Dispensing failed: {str(e)}")
    else:
        initial = {}
        if medicine:
            initial['medicine'] = medicine
        form = DispenseForm(initial=initial)
    
    context = {
        "title": "Dispense Medicine",
        "form": form,
        "medicine": medicine,
    }
    return render(request, "inventory_meds/dispense_medicine.html", context)


@login_required
def reports_dashboard(request):
    """Reports dashboard with visual analytics, supporting dynamic filtering via query parameters."""
    from datetime import datetime, timedelta
    from django.db.models import Count
    import json
    
    today = timezone.now().date()
    
    # ----------------------------------------------------
    # 1. APPLY FILTERS FROM REQUEST.GET
    # ----------------------------------------------------
    
    # Get date range from request (as strings, possibly None)
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    # Start with all medicines
    all_medicines = Medicine.objects.all()
    
    # Apply date filters to movement/dispensing data if present
    dispenses = DispenseRecord.objects.select_related('medicine', 'patient', 'dispensed_by').all()
    
    if start_date_str:
        # Convert string to date object
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            dispenses = dispenses.filter(dispensed_at__date__gte=start_date)
        except ValueError:
            pass # Ignore if date format is wrong
            
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            dispenses = dispenses.filter(dispensed_at__date__lte=end_date)
        except ValueError:
            pass # Ignore if date format is wrong


    # ----------------------------------------------------
    # 2. CALCULATE STATISTICS
    # ----------------------------------------------------
    
    # These counts are always based on the ENTIRE inventory, regardless of date range, 
    # unless you want to filter them too (e.g., if you had a 'Last Checked' date field).
    total_medicines = all_medicines.count()
    active_medicines = all_medicines.filter(status='active', quantity_on_hand__gt=0).count()
    low_stock_count = all_medicines.filter(quantity_on_hand__lte=F('reorder_level'), quantity_on_hand__gt=0).count()
    out_of_stock_count = all_medicines.filter(quantity_on_hand=0).count()
    
    # Expiry stats
    thirty_days_ahead = today + timedelta(days=30)
    ninety_days_ahead = today + timedelta(days=90)

    expired_count = all_medicines.filter(expires_on__lt=today).count()
    expiring_soon_count = all_medicines.filter(
        expires_on__gte=today,
        expires_on__lte=thirty_days_ahead
    ).count()
    
    critical_expiry = expiring_soon_count # Same definition as expiring_soon_count (within 30 days)
    
    valid_stock = all_medicines.filter(expires_on__gt=ninety_days_ahead).count()
    
    # Category distribution (always based on total inventory)
    category_data = all_medicines.values('category').annotate(count=Count('id')).order_by('-count')[:8]
    category_labels = [item['category'] for item in category_data]
    category_counts = [item['count'] for item in category_data]
    
    # Top medicines by stock (always based on current stock levels)
    top_medicines = all_medicines.order_by('-quantity_on_hand')[:8]
    top_medicines_names = [f"{m.name}" for m in top_medicines]
    top_medicines_stock = [m.quantity_on_hand for m in top_medicines]
    top_medicines_reorder = [m.reorder_level for m in top_medicines]

    # Expiring medicines timeline (next 90 days)
    expiring_medicines = all_medicines.filter(
        Q(expires_on__lt=today) | 
        Q(expires_on__gte=today, expires_on__lte=ninety_days_ahead) 
    ).order_by('expires_on')[:20]
    
    
    # ----------------------------------------------------
    # 3. CONDITIONAL RESPONSE
    # ----------------------------------------------------
    
    # Check if this is an AJAX request for dynamic updates
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'total_medicines': total_medicines,
            'active_medicines': active_medicines,
            'low_stock_count': low_stock_count,
            'out_of_stock_count': out_of_stock_count,
            'expired_count': expired_count,
            'expiring_soon_count': expiring_soon_count,
            'critical_expiry': critical_expiry,
            'valid_stock': valid_stock,
            
            # Chart Data - Return raw lists/data (JSON handles conversion)
            'category_labels': category_labels,
            'category_counts': category_counts,
            'top_medicines_names': top_medicines_names,
            'top_medicines_stock': top_medicines_stock,
            'top_medicines_reorder': top_medicines_reorder,
        })

    # If it's a regular request (initial load), render the HTML template
    context = {
        "title": "Medicine Inventory Reports",
        
        # Summary Stats
        "total_medicines": total_medicines,
        "active_medicines": active_medicines,
        "low_stock_count": low_stock_count,
        "out_of_stock_count": out_of_stock_count,
        "expired_count": expired_count,
        "expiring_soon_count": expiring_soon_count,
        "critical_expiry": critical_expiry,
        "valid_stock": valid_stock,
        
        # Chart Data - DUMP to JSON string for initial Django template embedding
        "category_labels": json.dumps(category_labels),
        "category_counts": json.dumps(category_counts),
        "top_medicines_names": json.dumps(top_medicines_names),
        "top_medicines_stock": json.dumps(top_medicines_stock),
        "top_medicines_reorder": json.dumps(top_medicines_reorder),
        
        # List data for the bottom section
        "expiring_medicines": expiring_medicines,

        # Pass filters back to the template to pre-fill the form (optional)
        "start_date": start_date_str, 
        "end_date": end_date_str,
    }
    return render(request, "inventory_meds/reports_dashboard.html", context)



@login_required
def inventory_summary_report(request):
    """Generate inventory summary report"""
    
    medicines = Medicine.objects.select_related('supplier').all()
    
    total_value = 0  # Could calculate if prices are added
    total_items = medicines.count()
    
    context = {
        "title": "Inventory Summary Report",
        "medicines": medicines,
        "total_items": total_items,
        "total_value": total_value,
        "generated_at": timezone.now(),
    }
    return render(request, "inventory_meds/report_inventory_summary.html", context)


@login_required
def low_stock_report(request):
    """Generate low stock report"""
    
    medicines = Medicine.objects.filter(
        quantity_on_hand__lte=F('reorder_level'),
        quantity_on_hand__gt=0
    ).select_related('supplier')
    
    context = {
        "title": "Low Stock Report",
        "medicines": medicines,
        "generated_at": timezone.now(),
    }
    return render(request, "inventory_meds/report_low_stock.html", context)


@login_required
def expiring_items_report(request):
    """Generate expiring items report"""
    
    thirty_days_ahead = timezone.now().date() + timedelta(days=30)
    medicines = Medicine.objects.filter(
        expires_on__lte=thirty_days_ahead,
        expires_on__gt=timezone.now().date()
    ).select_related('supplier').order_by('expires_on')
    
    context = {
        "title": "Expiring Items Report",
        "medicines": medicines,
        "generated_at": timezone.now(),
    }
    return render(request, "inventory_meds/report_expiring.html", context)


@login_required
def expired_items_report(request):
    """Generate expired items report"""
    
    medicines = Medicine.objects.filter(
        expires_on__lte=timezone.now().date()
    ).select_related('supplier').order_by('expires_on')
    
    context = {
        "title": "Expired Items Report",
        "medicines": medicines,
        "generated_at": timezone.now(),
    }
    return render(request, "inventory_meds/report_expired.html", context)


@login_required
def stock_movement_report(request):
    """Generate stock movement report"""
    
    # Get date range from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    movements = StockMovement.objects.select_related('medicine', 'performed_by').all()
    
    if start_date:
        movements = movements.filter(performed_at__gte=start_date)
    if end_date:
        movements = movements.filter(performed_at__lte=end_date)
    
    movements = movements.order_by('-performed_at')[:100]
    
    context = {
        "title": "Stock Movement Report",
        "movements": movements,
        "start_date": start_date,
        "end_date": end_date,
        "generated_at": timezone.now(),
    }
    return render(request, "inventory_meds/report_stock_movement.html", context)


@login_required
def dispensing_summary_report(request):
    """Generate dispensing summary report"""
    
    # Get date range from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    dispenses = DispenseRecord.objects.select_related(
        'medicine', 'patient', 'dispensed_by', 'prescribed_by'
    ).all()
    
    if start_date:
        dispenses = dispenses.filter(dispensed_at__gte=start_date)
    if end_date:
        dispenses = dispenses.filter(dispensed_at__lte=end_date)
    
    dispenses = dispenses.order_by('-dispensed_at')[:100]
    
    context = {
        "title": "Dispensing Summary Report",
        "dispenses": dispenses,
        "start_date": start_date,
        "end_date": end_date,
        "generated_at": timezone.now(),
    }
    return render(request, "inventory_meds/report_dispensing.html", context)


@login_required
def export_inventory_csv(request):
    """Export inventory to CSV"""
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="medicine_inventory.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Code', 'Name', 'Brand Name', 'Category', 'Form', 'Strength',
        'Manufacturer', 'Batch Number', 'Quantity', 'Reorder Level',
        'Expires On', 'Status', 'Supplier'
    ])
    
    medicines = Medicine.objects.select_related('supplier').all()
    for med in medicines:
        writer.writerow([
            med.code,
            med.name,
            med.brand_name,
            med.category,
            med.dosage_form,
            med.strength,
            med.manufacturer,
            med.batch_number,
            med.quantity_on_hand,
            med.reorder_level,
            med.expires_on,
            med.status,
            med.supplier.name if med.supplier else ''
        ])
    
    return response


@login_required
def audit_log_view(request):
    """View audit logs"""
    
    # TEMPORARY: Remove permission check to allow all users
    # if not check_permission(request.user, ['Admin', 'Auditor']):
    #     messages.error(request, "You do not have permission to view audit logs.")
    #     return HttpResponseForbidden("Access denied: insufficient privileges.")
    
    logs = MedicineAuditLog.objects.select_related('medicine', 'user', 'patient').order_by('-timestamp')[:200]
    
    context = {
        "title": "Medicine Inventory Audit Logs",
        "logs": logs,
    }
    return render(request, "inventory_meds/audit_logs.html", context)
