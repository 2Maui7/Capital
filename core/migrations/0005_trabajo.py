from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_pedido_usar_inventario'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Trabajo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad', models.IntegerField(verbose_name='Cantidad')),
                ('descripcion', models.TextField(verbose_name='Descripción del trabajo')),
                ('precio_unitario', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Precio unitario')),
                ('descuento', models.DecimalField(decimal_places=2, default=0, max_digits=5, verbose_name='Descuento (%)')),
                ('precio_total', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Precio total')),
                ('estado', models.CharField(choices=[('pendiente', 'Pendiente'), ('en_proceso', 'En Proceso'), ('en_produccion', 'En Producción'), ('terminado', 'Terminado'), ('entregado', 'Entregado'), ('cancelado', 'Cancelado')], default='pendiente', max_length=50, verbose_name='Estado')),
                ('fecha_creacion', models.DateField(auto_now_add=True, verbose_name='Fecha de creación')),
                ('fecha_entrega', models.DateField(verbose_name='Fecha de entrega estimada')),
                ('fecha_entregado', models.DateField(blank=True, null=True, verbose_name='Fecha de entrega real')),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='trabajos', to='core.cliente', verbose_name='Cliente')),
                ('producto', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='trabajos', to='core.producto', verbose_name='Producto/Trabajo')),
                ('usuario_registro', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='trabajos_registrados', to=settings.AUTH_USER_MODEL, verbose_name='Registrado por')),
            ],
            options={
                'verbose_name': 'Trabajo',
                'verbose_name_plural': 'Trabajos',
                'ordering': ['-fecha_creacion'],
            },
        ),
    ]
