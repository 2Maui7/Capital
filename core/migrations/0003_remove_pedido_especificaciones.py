from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_proveedor_compra'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pedido',
            name='especificaciones',
        ),
    ]
