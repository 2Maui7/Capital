
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_trabajo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trabajo',
            name='cantidad',
            field=models.IntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name='Cantidad'),
        ),
        migrations.AlterField(
            model_name='trabajo',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
