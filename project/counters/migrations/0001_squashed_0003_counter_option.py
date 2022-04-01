# Generated by Django 4.0.3 on 2022-03-18 10:02

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.db.models import F
from django.db.models.functions import Round


def convert_beer_to_av(apps, schema_editor):
    Counter = apps.get_model('counters', 'Counter')
    Counter.objects.filter(counter_type='drinks').update(quantity=Round(F('quantity') * 2.5, 2), option='beer')

# Functions from the following migrations need manual copying.
# Move them and any dependencies into this file, then update the
# RunPython operations to refer to the local versions:
# project.counters.migrations.0003_counter_option

class Migration(migrations.Migration):

    replaces = [('counters', '0001_initial'), ('counters', '0002_auto_20200726_2137'), ('counters', '0003_counter_option')]

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Counter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('quantity', models.FloatField(validators=[django.core.validators.MinValueValidator(0.1)])),
                ('counter_type', models.CharField(max_length=254, validators=[django.core.validators.MinLengthValidator(3)])),
                ('user', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('option', models.CharField(blank=True, max_length=16, null=True)),
            ],
            options={
                'ordering': ['-date'],
                'get_latest_by': ['date'],
            },
        ),
        migrations.RunPython(convert_beer_to_av),
    ]