from django.contrib import admin
from .models import Supplier, Medicine, StockMovement, DispenseRecord, MedicineAuditLog


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_email', 'contact_phone', 'created_at']
    search_fields = ['name', 'contact_email']
    list_filter = ['created_at']


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'brand_name', 'category', 'dosage_form', 
                   'strength', 'quantity_on_hand', 'reorder_level', 'expires_on', 'status']
    search_fields = ['code', 'name', 'brand_name', 'category', 'batch_number', 'manufacturer']
    list_filter = ['status', 'category', 'dosage_form', 'prescription_only', 'created_at']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'brand_name', 'description', 'category', 
                      'dosage_form', 'strength', 'unit')
        }),
        ('Manufacturer & Batch', {
            'fields': ('manufacturer', 'batch_number', 'lot_number', 'supplier')
        }),
        ('Dates', {
            'fields': ('date_received', 'expires_on')
        }),
        ('Inventory', {
            'fields': ('quantity_on_hand', 'quantity_reserved', 'reorder_level')
        }),
        ('Storage & Usage', {
            'fields': ('storage_instructions', 'prescription_only', 'status')
        }),
        ('Additional', {
            'fields': ('notes', 'created_at', 'updated_at')
        }),
    )


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['medicine', 'movement_type', 'quantity', 'performed_by', 'performed_at', 'reason']
    search_fields = ['medicine__name', 'reference', 'reason']
    list_filter = ['movement_type', 'performed_at']
    readonly_fields = ['created_at']
    raw_id_fields = ['medicine', 'performed_by']


@admin.register(DispenseRecord)
class DispenseRecordAdmin(admin.ModelAdmin):
    list_display = ['medicine', 'patient', 'quantity', 'dispensed_by', 'dispensed_at']
    search_fields = ['medicine__name', 'patient__first_name', 'patient__last_name']
    list_filter = ['dispensed_at']
    readonly_fields = ['created_at', 'stock_before', 'stock_after']
    raw_id_fields = ['medicine', 'patient', 'prescribed_by', 'dispensed_by', 'visit_log']


@admin.register(MedicineAuditLog)
class MedicineAuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'medicine', 'user', 'timestamp', 'field_name']
    search_fields = ['medicine__name', 'user__user__username', 'reason']
    list_filter = ['action', 'timestamp']
    readonly_fields = ['timestamp']
    raw_id_fields = ['medicine', 'user', 'patient']
    
    def has_add_permission(self, request):
        # Audit logs should not be manually created
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Audit logs should not be deleted
        return False
