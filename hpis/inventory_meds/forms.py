from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Medicine, StockMovement, DispenseRecord, Supplier


class MedicineForm(forms.ModelForm):
    """Form for creating and editing medicine entries"""
    
    class Meta:
        model = Medicine
        fields = [
            'code', 'name', 'brand_name', 'description', 'category', 
            'dosage_form', 'strength', 'unit', 'manufacturer', 
            'batch_number', 'lot_number', 'date_received', 'expires_on',
            'quantity_on_hand', 'reorder_level', 'storage_instructions',
            'prescription_only', 'supplier', 'notes'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., MED001'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Generic name'}),
            'brand_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brand/trade name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('', 'Select Category'),
                ('Antibiotic', 'Antibiotic'),
                ('Analgesic', 'Analgesic'),
                ('Antipyretic', 'Antipyretic'),
                ('Antihistamine', 'Antihistamine'),
                ('Anti-inflammatory', 'Anti-inflammatory'),
                ('Antiviral', 'Antiviral'),
                ('Antifungal', 'Antifungal'),
                ('Cardiovascular', 'Cardiovascular'),
                ('Gastrointestinal', 'Gastrointestinal'),
                ('Respiratory', 'Respiratory'),
                ('Vitamin/Supplement', 'Vitamin/Supplement'),
                ('Other', 'Other'),
            ]),
            'dosage_form': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('', 'Select Form'),
                ('Tablet', 'Tablet'),
                ('Capsule', 'Capsule'),
                ('Syrup', 'Syrup'),
                ('Suspension', 'Suspension'),
                ('Injection', 'Injection'),
                ('Ointment', 'Ointment'),
                ('Cream', 'Cream'),
                ('Drops', 'Drops'),
                ('Inhaler', 'Inhaler'),
                ('Patch', 'Patch'),
                ('Other', 'Other'),
            ]),
            'strength': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 500mg, 5mg/mL'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., tablet, bottle'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control'}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Batch number'}),
            'lot_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Lot number'}),
            'date_received': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expires_on': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'quantity_on_hand': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'reorder_level': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'storage_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 
                                                         'placeholder': 'e.g., Store at room temperature'}),
            'prescription_only': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def clean_expires_on(self):
        expires_on = self.cleaned_data.get('expires_on')
        if expires_on and expires_on < timezone.now().date():
            raise ValidationError("Expiration date must be a future date.")
        return expires_on
    
    def clean_quantity_on_hand(self):
        quantity = self.cleaned_data.get('quantity_on_hand')
        if quantity is None or quantity < 0:
            raise ValidationError("Quantity must be a positive integer.")
        return quantity
    
    def clean_batch_number(self):
        batch_number = self.cleaned_data.get('batch_number')
        name = self.cleaned_data.get('name')
        
        if batch_number and name:
            # Check for duplicate batch number for the same medicine
            existing = Medicine.objects.filter(
                name=name, 
                batch_number=batch_number
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing.exists():
                raise ValidationError(
                    f"Batch number '{batch_number}' already exists for medicine '{name}'."
                )
        return batch_number


class MedicineEditForm(forms.ModelForm):
    """Form for editing existing medicine (restricted fields)"""
    
    class Meta:
        model = Medicine
        fields = [
            'description', 'category', 'manufacturer', 'batch_number', 
            'lot_number', 'expires_on', 'quantity_on_hand', 'reorder_level',
            'storage_instructions', 'supplier', 'notes'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control'}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control'}),
            'lot_number': forms.TextInput(attrs={'class': 'form-control'}),
            'expires_on': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'quantity_on_hand': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'reorder_level': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'storage_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class StockAdjustmentForm(forms.Form):
    """Form for adjusting medicine stock"""
    
    ADJUSTMENT_TYPES = [
        ('add', 'Add Stock (Restocking)'),
        ('reduce', 'Reduce Stock (Manual Adjustment)'),
        ('spoilage', 'Deduct - Spoilage/Breakage'),
        ('expiration', 'Deduct - Expiration'),
    ]
    
    adjustment_type = forms.ChoiceField(
        choices=ADJUSTMENT_TYPES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Quantity'})
    )
    reason = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 
                                    'placeholder': 'Reason for adjustment (required)'})
    )
    batch_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Batch number (optional)'})
    )
    
    def __init__(self, *args, medicine=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.medicine = medicine
    
    def clean(self):
        cleaned_data = super().clean()
        adjustment_type = cleaned_data.get('adjustment_type')
        quantity = cleaned_data.get('quantity')
        
        if self.medicine and adjustment_type in ['reduce', 'spoilage', 'expiration']:
            if quantity > self.medicine.quantity_on_hand:
                raise ValidationError(
                    f"Cannot reduce by {quantity}. Only {self.medicine.quantity_on_hand} in stock."
                )
        
        return cleaned_data


class DispenseForm(forms.ModelForm):
    """Form for dispensing medicine to patients"""
    
    class Meta:
        model = DispenseRecord
        fields = ['medicine', 'patient', 'quantity', 'instructions']
        widgets = {
            'medicine': forms.Select(attrs={'class': 'form-control'}),
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 
                                                  'placeholder': 'Dosage and usage instructions'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter to show only active medicines with stock
        self.fields['medicine'].queryset = Medicine.objects.filter(
            status=Medicine.STATUS_ACTIVE,
            quantity_on_hand__gt=0
        ).exclude(status=Medicine.STATUS_EXPIRED)
    
    def clean(self):
        cleaned_data = super().clean()
        medicine = cleaned_data.get('medicine')
        quantity = cleaned_data.get('quantity')
        
        if medicine and quantity:
            # Check if medicine is expired
            if medicine.is_expired:
                raise ValidationError(
                    f"Cannot dispense expired medicine: {medicine.name}"
                )
            
            # Check if medicine is archived
            if medicine.status == Medicine.STATUS_DISCONTINUED:
                raise ValidationError(
                    f"Cannot dispense archived medicine: {medicine.name}"
                )
            
            # Check stock availability
            available = medicine.available_quantity
            if quantity > available:
                raise ValidationError(
                    f"Insufficient stock for medicine: {medicine.name}. Available: {available}"
                )
        
        return cleaned_data


class SupplierForm(forms.ModelForm):
    """Form for managing suppliers"""
    
    class Meta:
        model = Supplier
        fields = ['name', 'contact_email', 'contact_phone', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class SearchFilterForm(forms.Form):
    """Form for searching and filtering medicines"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 
                                     'placeholder': 'Search by name, category, batch...'})
    )
    category = forms.ChoiceField(
        required=False,
        choices=[('', 'All Categories')] + [
            ('Antibiotic', 'Antibiotic'),
            ('Analgesic', 'Analgesic'),
            ('Antipyretic', 'Antipyretic'),
            ('Antihistamine', 'Antihistamine'),
            ('Anti-inflammatory', 'Anti-inflammatory'),
            ('Other', 'Other'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Status')] + Medicine.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    stock_filter = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Stock Levels'),
            ('low', 'Low Stock'),
            ('out', 'Out of Stock'),
            ('adequate', 'Adequate Stock'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    expiry_filter = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Expiry Status'),
            ('expiring_soon', 'Expiring Soon (30 days)'),
            ('expired', 'Expired'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    prescription_only = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Types'),
            ('yes', 'Prescription Only'),
            ('no', 'Over-the-Counter'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
