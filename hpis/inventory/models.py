from django.db import models
from django.conf import settings


class Supplier(models.Model):
    name = models.CharField(max_length=255, unique=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.name


class Medicine(models.Model):
    code = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    dosage = models.CharField(max_length=100, blank=True)
    form = models.CharField(max_length=100, blank=True)  # e.g., tablet, syrup
    unit = models.CharField(max_length=50, default="pcs")
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    expiration_date = models.DateField(blank=True, null=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["is_active", "expiration_date"]),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class StockMovement(models.Model):
    IN = "IN"
    OUT = "OUT"
    MOVEMENT_TYPES = [
        (IN, "Stock In"),
        (OUT, "Stock Out"),
    ]

    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name="movements")
    movement_type = models.CharField(max_length=3, choices=MOVEMENT_TYPES)
    quantity = models.PositiveIntegerField()
    reference = models.CharField(max_length=255, blank=True)  # e.g., PO#, Dispense ID
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["medicine", "timestamp"]),
            models.Index(fields=["movement_type", "timestamp"]),
        ]


class DispenseRecord(models.Model):
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT, related_name="dispenses")
    patient_name = models.CharField(max_length=255)
    patient_id = models.CharField(max_length=100, blank=True)  # link later to PatientRecord
    quantity = models.PositiveIntegerField()
    prescribed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="prescriptions")
    dispensed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="dispenses")
    dispensed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["dispensed_at"]),
            models.Index(fields=["patient_id", "dispensed_at"]),
        ]
