from django.db import migrations
from datetime import date

def generate_codes(apps, schema_editor):
    PatientRecord = apps.get_model('records', 'PatientRecord')
    year = date.today().year
    for record in PatientRecord.objects.all():
        if not record.patient_code:
            record.patient_code = f"PAT-{year}-{str(record.id).zfill(3)}"
            record.save()

class Migration(migrations.Migration):

    dependencies = [
        ('records', '0005_patientrecord_patient_code'),  # adjust if your last migration number differs
    ]

    operations = [
        migrations.RunPython(generate_codes),
    ]