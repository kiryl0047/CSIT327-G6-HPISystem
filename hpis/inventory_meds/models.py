from django.db import models
from django.utils import timezone

# Avoid repeated string literals for relations
USER_PROFILE_REL = "main.UserProfile"


class Supplier(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Medicine(models.Model):
    STATUS_ACTIVE = "Active"
    STATUS_OUT_OF_STOCK = "Out of Stock"
    STATUS_EXPIRED = "Expired"
    STATUS_DISCONTINUED = "Discontinued"
    
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_OUT_OF_STOCK, "Out of Stock"),
        (STATUS_EXPIRED, "Expired"),
        (STATUS_DISCONTINUED, "Discontinued"),
    ]
    
    # Basic Information
    code = models.CharField(max_length=32, unique=True, db_index=True)
    name = models.CharField(max_length=255, db_index=True, help_text="Generic medicine name")
    brand_name = models.CharField(max_length=255, blank=True, help_text="Brand/trade name")
    description = models.TextField(blank=True, help_text="Detailed description of the medicine")
    category = models.CharField(max_length=100, blank=True, db_index=True, 
                                help_text="e.g., Antibiotic, Analgesic, Antipyretic")
    dosage_form = models.CharField(max_length=100, blank=True, 
                                   help_text="e.g., Tablet, Syrup, Capsule, Ointment, Injection")
    strength = models.CharField(max_length=100, blank=True, 
                               help_text="e.g., 500mg, 5mg/mL")
    unit = models.CharField(max_length=50, default="tablet")
    
    # Manufacturer and Batch Information
    manufacturer = models.CharField(max_length=255, blank=True)
    batch_number = models.CharField(max_length=100, blank=True, db_index=True)
    lot_number = models.CharField(max_length=100, blank=True)
    
    # Dates
    date_received = models.DateField(blank=True, null=True)
    expires_on = models.DateField(blank=True, null=True, db_index=True)
    
    # Inventory fields
    quantity_on_hand = models.PositiveIntegerField(default=0)
    quantity_reserved = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=0, 
                                               help_text="Minimum quantity before reorder alert")
    
    # Storage and Usage
    storage_instructions = models.TextField(blank=True, 
                                          help_text="Storage temperature, conditions, etc.")
    prescription_only = models.BooleanField(default=False, 
                                           help_text="True if prescription required, False for OTC")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, 
                             default=STATUS_ACTIVE, db_index=True)
    
    # Relations
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, blank=True, null=True, related_name="medicines")
    
    # Additional Info
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["name", "category"]),
            models.Index(fields=["expires_on"]),
            models.Index(fields=["batch_number"]),
            models.Index(fields=["status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'dosage_form', 'strength', 'batch_number'],
                name='unique_medicine_batch'
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.strength or ''} {self.dosage_form or ''})".strip()

    def save(self, *args, **kwargs):
        # Auto-update status based on quantity and expiration
        if self.quantity_on_hand == 0:
            self.status = self.STATUS_OUT_OF_STOCK
        elif self.expires_on and self.expires_on <= timezone.now().date():
            self.status = self.STATUS_EXPIRED
        elif self.status == self.STATUS_OUT_OF_STOCK and self.quantity_on_hand > 0:
            self.status = self.STATUS_ACTIVE
        super().save(*args, **kwargs)

    @property
    def is_low_stock(self) -> bool:
        return self.quantity_on_hand <= self.reorder_level and self.quantity_on_hand > 0

    @property
    def is_expiring_soon(self) -> bool:
        if not self.expires_on:
            return False
        return self.expires_on <= (timezone.now().date() + timezone.timedelta(days=30)) and self.expires_on > timezone.now().date()
    
    @property
    def is_expired(self) -> bool:
        if not self.expires_on:
            return False
        return self.expires_on <= timezone.now().date()
    
    @property
    def available_quantity(self) -> int:
        """Quantity available for dispensing (on hand minus reserved)"""
        return max(0, self.quantity_on_hand - self.quantity_reserved)


class StockMovement(models.Model):
    MOVEMENT_IN = "IN"
    MOVEMENT_OUT = "OUT"
    MOVEMENT_ADJUST = "ADJUST"
    MOVEMENT_TYPES = (
        (MOVEMENT_IN, "Received"),
        (MOVEMENT_OUT, "Dispensed"),
        (MOVEMENT_ADJUST, "Adjusted"),
    )

    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name="movements")
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_TYPES, db_index=True)
    quantity = models.IntegerField()  # allow negative for adjustments; validated in code
    reason = models.CharField(max_length=255, blank=True)
    reference = models.CharField(max_length=100, blank=True, db_index=True)  # e.g., prescription or visit code
    performed_by = models.ForeignKey(USER_PROFILE_REL, on_delete=models.SET_NULL, blank=True, null=True, related_name="stock_movements")
    performed_at = models.DateTimeField(default=timezone.now, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-performed_at", "-id"]
        indexes = [
            models.Index(fields=["movement_type", "performed_at"]),
            models.Index(fields=["medicine", "performed_at"]),
        ]

    def __str__(self):
        return f"{self.movement_type} {self.quantity} {self.medicine.name}"


class DispenseRecord(models.Model):
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT, related_name="dispenses")
    patient = models.ForeignKey("records.PatientRecord", on_delete=models.PROTECT, related_name="dispenses")
    quantity = models.PositiveIntegerField()
    prescribed_by = models.ForeignKey(USER_PROFILE_REL, on_delete=models.SET_NULL, blank=True, null=True, related_name="prescriptions")
    dispensed_by = models.ForeignKey(USER_PROFILE_REL, on_delete=models.SET_NULL, blank=True, null=True, related_name="dispensed_items")
    visit_log = models.ForeignKey("records.VisitLog", on_delete=models.SET_NULL, blank=True, null=True, related_name="dispensed_items")
    instructions = models.TextField(blank=True)
    dispensed_at = models.DateTimeField(default=timezone.now, db_index=True)
    
    # Stock tracking
    stock_before = models.PositiveIntegerField(default=0)
    stock_after = models.PositiveIntegerField(default=0)
    batch_number = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-dispensed_at", "-id"]
        indexes = [
            models.Index(fields=["medicine", "dispensed_at"]),
            models.Index(fields=["patient", "dispensed_at"]),
        ]

    def __str__(self):
        return f"Dispensed {self.quantity} {self.medicine.name} to {self.patient.full_name}"


class MedicineAuditLog(models.Model):
    ACTION_CREATE = "CREATE"
    ACTION_UPDATE = "UPDATE"
    ACTION_DELETE = "DELETE"
    ACTION_ARCHIVE = "ARCHIVE"
    ACTION_STOCK_ADD = "STOCK_ADD"
    ACTION_STOCK_REDUCE = "STOCK_REDUCE"
    ACTION_DISPENSE = "DISPENSE"
    ACTION_ACCESS_DENIED = "ACCESS_DENIED"
    
    ACTION_CHOICES = [
        (ACTION_CREATE, "Created"),
        (ACTION_UPDATE, "Updated"),
        (ACTION_DELETE, "Deleted"),
        (ACTION_ARCHIVE, "Archived"),
        (ACTION_STOCK_ADD, "Stock Added"),
        (ACTION_STOCK_REDUCE, "Stock Reduced"),
        (ACTION_DISPENSE, "Dispensed"),
        (ACTION_ACCESS_DENIED, "Access Denied"),
    ]
    
    medicine = models.ForeignKey(Medicine, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, db_index=True)
    user = models.ForeignKey(USER_PROFILE_REL, on_delete=models.SET_NULL, null=True, blank=True, related_name="medicine_audit_logs")
    field_name = models.CharField(max_length=100, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    reason = models.TextField(blank=True)
    patient = models.ForeignKey("records.PatientRecord", on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["action", "timestamp"]),
            models.Index(fields=["medicine", "timestamp"]),
            models.Index(fields=["user", "timestamp"]),
        ]
    
    def __str__(self):
        return f"{self.action} by {self.user} at {self.timestamp}"
