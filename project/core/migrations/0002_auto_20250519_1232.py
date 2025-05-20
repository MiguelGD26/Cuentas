from django.db import migrations

def agregar_tipos_documento(apps, schema_editor):
    TipoDocumento = apps.get_model('core', 'TipoDocumento')
    TipoDocumento.objects.get_or_create(nombre='Factura')
    TipoDocumento.objects.get_or_create(nombre='Boleta')

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(agregar_tipos_documento),
    ]