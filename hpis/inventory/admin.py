from django.contrib import admin
from .models import Supplier, Medicine, StockMovement, DispenseRecord


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_email", "contact_phone")
    search_fields = ("name",)


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "form", "unit", "price_per_unit", "expiration_date", "is_active")
    list_filter = ("form", "is_active")
    search_fields = ("code", "name")


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("medicine", "movement_type", "quantity", "reference", "performed_by", "timestamp")
    list_filter = ("movement_type",)
    search_fields = ("reference",)


@admin.register(DispenseRecord)
class DispenseRecordAdmin(admin.ModelAdmin):
    list_display = ("medicine", "patient_name", "patient_id", "quantity", "prescribed_by", "dispensed_by", "dispensed_at")
    search_fields = ("patient_name", "patient_id")
