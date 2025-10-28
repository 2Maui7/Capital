from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_remove_pedido_especificaciones'),
    ]

    operations = [
        migrations.AddField(
            model_name='pedido',
            name='inventario',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pedidos', to='core.inventario', verbose_name='Material'),
        ),
        migrations.RemoveField(
            model_name='pedido',
            name='producto',
        ),
    ]