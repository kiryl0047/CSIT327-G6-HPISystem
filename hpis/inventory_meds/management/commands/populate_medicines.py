from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from inventory_meds.models import Medicine, Supplier
from decimal import Decimal
import random


class Command(BaseCommand):
    help = 'Populate the database with common clinic medicines'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting to populate medicine database...')

        # Create suppliers
        suppliers = {
            'generic': Supplier.objects.get_or_create(
                name='Generic Pharmaceuticals',
                defaults={
                    'contact_phone': '555-0100',
                    'contact_email': 'generic@pharma.com',
                    'address': '123 Medical Plaza'
                }
            )[0],
            'brand': Supplier.objects.get_or_create(
                name='Premium Healthcare Inc.',
                defaults={
                    'contact_phone': '555-0200',
                    'contact_email': 'premium@healthcare.com',
                    'address': '456 Health Street'
                }
            )[0],
            'local': Supplier.objects.get_or_create(
                name='Local Medical Supply',
                defaults={
                    'contact_phone': '555-0300',
                    'contact_email': 'local@medical.com',
                    'address': '789 Clinic Avenue'
                }
            )[0],
        }
        
        # Define expiration scenarios for diverse status reporting
        expiration_scenarios = [
            ('expired', -90),  # Expired 3 months ago
            ('expired', -60),  # Expired 2 months ago
            ('expired', -30),  # Expired 1 month ago
            ('expired', -15),  # Expired 2 weeks ago
            ('near_expiry', 15),  # Expires in 2 weeks
            ('near_expiry', 30),  # Expires in 1 month
            ('near_expiry', 60),  # Expires in 2 months
            ('active', 180),  # Expires in 6 months
            ('active', 365),  # Expires in 1 year
            ('active', 730),  # Expires in 2 years
        ]

        # Common clinic medicines data
        medicines_data = [
            # Pain Relief & Fever
            {
                'name': 'Paracetamol',
                'brand_name': 'Biogesic',
                'category': 'Analgesic/Antipyretic',
                'dosage_form': 'Tablet',
                'strength': '500mg',
                'manufacturer': 'United Laboratories',
                'quantity_on_hand': 500,
                'reorder_level': 100,
                'prescription_only': False,
                'supplier': suppliers['generic'],
            },
            {
                'name': 'Ibuprofen',
                'brand_name': 'Advil',
                'category': 'NSAID',
                'dosage_form': 'Tablet',
                'strength': '200mg',
                'manufacturer': 'Pfizer',
                'quantity_on_hand': 300,
                'reorder_level': 80,
                'prescription_only': False,
                'supplier': suppliers['brand'],
            },
            {
                'name': 'Mefenamic Acid',
                'brand_name': 'Ponstan',
                'category': 'NSAID',
                'dosage_form': 'Capsule',
                'strength': '250mg',
                'manufacturer': 'Pfizer',
                'quantity_on_hand': 200,
                'reorder_level': 60,
                'prescription_only': True,
                'supplier': suppliers['brand'],
            },

            # Antibiotics
            {
                'name': 'Amoxicillin',
                'brand_name': 'Amoxil',
                'category': 'Antibiotic',
                'dosage_form': 'Capsule',
                'strength': '500mg',
                'manufacturer': 'GlaxoSmithKline',
                'quantity_on_hand': 250,
                'reorder_level': 70,
                'prescription_only': True,
                'supplier': suppliers['brand'],
            },
            {
                'name': 'Cefalexin',
                'brand_name': 'Keflex',
                'category': 'Antibiotic',
                'dosage_form': 'Capsule',
                'strength': '500mg',
                'manufacturer': 'Generic Pharma',
                'quantity_on_hand': 180,
                'reorder_level': 50,
                'prescription_only': True,
                'supplier': suppliers['generic'],
            },
            {
                'name': 'Azithromycin',
                'brand_name': 'Zithromax',
                'category': 'Antibiotic',
                'dosage_form': 'Tablet',
                'strength': '500mg',
                'manufacturer': 'Pfizer',
                'quantity_on_hand': 150,
                'reorder_level': 40,
                'prescription_only': True,
                'supplier': suppliers['brand'],
            },

            # Cold & Flu
            {
                'name': 'Cetirizine',
                'brand_name': 'Zyrtec',
                'category': 'Antihistamine',
                'dosage_form': 'Tablet',
                'strength': '10mg',
                'manufacturer': 'UCB Pharma',
                'quantity_on_hand': 400,
                'reorder_level': 100,
                'prescription_only': False,
                'supplier': suppliers['generic'],
            },
            {
                'name': 'Loratadine',
                'brand_name': 'Claritin',
                'category': 'Antihistamine',
                'dosage_form': 'Tablet',
                'strength': '10mg',
                'manufacturer': 'Bayer',
                'quantity_on_hand': 350,
                'reorder_level': 90,
                'prescription_only': False,
                'supplier': suppliers['brand'],
            },
            {
                'name': 'Carbocisteine',
                'brand_name': 'Solmux',
                'category': 'Mucolytic',
                'dosage_form': 'Capsule',
                'strength': '500mg',
                'manufacturer': 'United Laboratories',
                'quantity_on_hand': 300,
                'reorder_level': 80,
                'prescription_only': False,
                'supplier': suppliers['generic'],
            },

            # Gastrointestinal
            {
                'name': 'Omeprazole',
                'brand_name': 'Losec',
                'category': 'Proton Pump Inhibitor',
                'dosage_form': 'Capsule',
                'strength': '20mg',
                'manufacturer': 'AstraZeneca',
                'quantity_on_hand': 200,
                'reorder_level': 60,
                'prescription_only': True,
                'supplier': suppliers['brand'],
            },
            {
                'name': 'Loperamide',
                'brand_name': 'Imodium',
                'category': 'Anti-diarrheal',
                'dosage_form': 'Capsule',
                'strength': '2mg',
                'manufacturer': 'Johnson & Johnson',
                'quantity_on_hand': 250,
                'reorder_level': 70,
                'prescription_only': False,
                'supplier': suppliers['brand'],
            },
            {
                'name': 'Aluminum Hydroxide',
                'brand_name': 'Kremil-S',
                'category': 'Antacid',
                'dosage_form': 'Tablet',
                'strength': '178mg',
                'manufacturer': 'United Laboratories',
                'quantity_on_hand': 400,
                'reorder_level': 100,
                'prescription_only': False,
                'supplier': suppliers['local'],
            },

            # Vitamins & Supplements
            {
                'name': 'Ascorbic Acid',
                'brand_name': 'Vitamin C',
                'category': 'Vitamin',
                'dosage_form': 'Tablet',
                'strength': '500mg',
                'manufacturer': 'Generic Pharma',
                'quantity_on_hand': 600,
                'reorder_level': 150,
                'prescription_only': False,
                'supplier': suppliers['generic'],
            },
            {
                'name': 'Multivitamins',
                'brand_name': 'Centrum',
                'category': 'Vitamin',
                'dosage_form': 'Tablet',
                'strength': 'Adult Formula',
                'manufacturer': 'Pfizer',
                'quantity_on_hand': 300,
                'reorder_level': 80,
                'prescription_only': False,
                'supplier': suppliers['brand'],
            },
            {
                'name': 'Ferrous Sulfate',
                'brand_name': 'Iberet',
                'category': 'Iron Supplement',
                'dosage_form': 'Tablet',
                'strength': '325mg',
                'manufacturer': 'Abbott',
                'quantity_on_hand': 250,
                'reorder_level': 70,
                'prescription_only': False,
                'supplier': suppliers['brand'],
            },

            # Cardiovascular
            {
                'name': 'Amlodipine',
                'brand_name': 'Norvasc',
                'category': 'Antihypertensive',
                'dosage_form': 'Tablet',
                'strength': '5mg',
                'manufacturer': 'Pfizer',
                'quantity_on_hand': 200,
                'reorder_level': 50,
                'prescription_only': True,
                'supplier': suppliers['brand'],
            },
            {
                'name': 'Losartan',
                'brand_name': 'Cozaar',
                'category': 'Antihypertensive',
                'dosage_form': 'Tablet',
                'strength': '50mg',
                'manufacturer': 'Merck',
                'quantity_on_hand': 180,
                'reorder_level': 50,
                'prescription_only': True,
                'supplier': suppliers['brand'],
            },
            {
                'name': 'Atorvastatin',
                'brand_name': 'Lipitor',
                'category': 'Statin',
                'dosage_form': 'Tablet',
                'strength': '20mg',
                'manufacturer': 'Pfizer',
                'quantity_on_hand': 150,
                'reorder_level': 40,
                'prescription_only': True,
                'supplier': suppliers['brand'],
            },

            # Diabetes
            {
                'name': 'Metformin',
                'brand_name': 'Glucophage',
                'category': 'Antidiabetic',
                'dosage_form': 'Tablet',
                'strength': '500mg',
                'manufacturer': 'Merck',
                'quantity_on_hand': 300,
                'reorder_level': 80,
                'prescription_only': True,
                'supplier': suppliers['brand'],
            },
            {
                'name': 'Glimepiride',
                'brand_name': 'Amaryl',
                'category': 'Antidiabetic',
                'dosage_form': 'Tablet',
                'strength': '2mg',
                'manufacturer': 'Sanofi',
                'quantity_on_hand': 150,
                'reorder_level': 40,
                'prescription_only': True,
                'supplier': suppliers['brand'],
            },

            # Topical & Dermatological
            {
                'name': 'Betamethasone',
                'brand_name': 'Celestone',
                'category': 'Corticosteroid',
                'dosage_form': 'Cream',
                'strength': '0.1%',
                'manufacturer': 'Merck',
                'quantity_on_hand': 100,
                'reorder_level': 30,
                'prescription_only': True,
                'supplier': suppliers['brand'],
            },
            {
                'name': 'Povidone-Iodine',
                'brand_name': 'Betadine',
                'category': 'Antiseptic',
                'dosage_form': 'Solution',
                'strength': '10%',
                'manufacturer': 'Mundipharma',
                'quantity_on_hand': 150,
                'reorder_level': 40,
                'prescription_only': False,
                'supplier': suppliers['local'],
            },

            # Respiratory
            {
                'name': 'Salbutamol',
                'brand_name': 'Ventolin',
                'category': 'Bronchodilator',
                'dosage_form': 'Inhaler',
                'strength': '100mcg',
                'manufacturer': 'GlaxoSmithKline',
                'quantity_on_hand': 80,
                'reorder_level': 20,
                'prescription_only': True,
                'supplier': suppliers['brand'],
            },
            {
                'name': 'Montelukast',
                'brand_name': 'Singulair',
                'category': 'Leukotriene Inhibitor',
                'dosage_form': 'Tablet',
                'strength': '10mg',
                'manufacturer': 'Merck',
                'quantity_on_hand': 120,
                'reorder_level': 35,
                'prescription_only': True,
                'supplier': suppliers['brand'],
            },

            # Other Common Medications
            {
                'name': 'Dextromethorphan',
                'brand_name': 'Robitussin',
                'category': 'Cough Suppressant',
                'dosage_form': 'Syrup',
                'strength': '15mg/5mL',
                'manufacturer': 'Pfizer',
                'quantity_on_hand': 200,
                'reorder_level': 50,
                'prescription_only': False,
                'supplier': suppliers['brand'],
            },
            {
                'name': 'Dexamethasone',
                'brand_name': 'Decadron',
                'category': 'Corticosteroid',
                'dosage_form': 'Tablet',
                'strength': '0.5mg',
                'manufacturer': 'Merck',
                'quantity_on_hand': 100,
                'reorder_level': 30,
                'prescription_only': True,
                'supplier': suppliers['brand'],
            },
            {
                'name': 'Hyoscine',
                'brand_name': 'Buscopan',
                'category': 'Antispasmodic',
                'dosage_form': 'Tablet',
                'strength': '10mg',
                'manufacturer': 'Boehringer Ingelheim',
                'quantity_on_hand': 150,
                'reorder_level': 40,
                'prescription_only': False,
                'supplier': suppliers['brand'],
            },
        ]

        # Create medicines
        created_count = 0
        updated_count = 0
        
        for index, med_data in enumerate(medicines_data):
            # Generate unique code
            code = f"MED{Medicine.objects.count() + 1:05d}"
            
            # Generate batch number
            batch_number = f"BATCH{created_count + 1:04d}"
            
            # Assign expiration scenario based on index to ensure diversity
            scenario_index = index % len(expiration_scenarios)
            status_type, days_offset = expiration_scenarios[scenario_index]
            
            # Set expiration date based on scenario
            expires_on = timezone.now().date() + timedelta(days=days_offset)
            
            # Set status based on expiration
            if status_type == 'expired':
                status = 'expired'
            elif status_type == 'near_expiry':
                status = 'active'  # Still active but will show as near expiry in reports
            else:
                status = 'active'
            
            # Adjust quantity for expired items (some should be low/zero)
            if status == 'expired':
                # Some expired items still have stock (need disposal), some are depleted
                original_qty = med_data['quantity_on_hand']
                med_data['quantity_on_hand'] = random.choice([0, original_qty // 4, original_qty // 2])
            
            # Check if medicine already exists
            existing = Medicine.objects.filter(
                name=med_data['name'],
                strength=med_data['strength']
            ).first()
            
            if existing:
                # Update existing medicine
                for key, value in med_data.items():
                    setattr(existing, key, value)
                existing.batch_number = batch_number
                existing.expires_on = expires_on
                existing.status = status
                existing.save()
                updated_count += 1
                self.stdout.write(f'  Updated: {existing.name} ({existing.strength}) - Status: {status}, Expires: {expires_on}')
            else:
                # Create new medicine
                Medicine.objects.create(
                    code=code,
                    batch_number=batch_number,
                    expires_on=expires_on,
                    date_received=timezone.now().date() - timedelta(days=random.randint(30, 365)),
                    status=status,
                    **med_data
                )
                created_count += 1
                self.stdout.write(f'  Created: {med_data["name"]} ({med_data["strength"]}) - Status: {status}, Expires: {expires_on}')

        self.stdout.write(self.style.SUCCESS(
            f'\nSuccessfully populated medicine database!\n'
            f'Created: {created_count} medicines\n'
            f'Updated: {updated_count} medicines\n'
            f'Total: {Medicine.objects.count()} medicines in database'
        ))
