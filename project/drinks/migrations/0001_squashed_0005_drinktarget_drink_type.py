# Generated by Django 4.0.3 on 2022-03-18 09:37

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.db.models import F
from django.db.models.functions import Round


def convert_beer_to_av(apps, schema_editor):
    DrinkTarget = apps.get_model('drinks', 'DrinkTarget')
    DrinkTarget.objects.all().update(quantity=Round((F('quantity') * 2.5)/500, 2), drink_type='beer')

# Functions from the following migrations need manual copying.
# Move them and any dependencies into this file, then update the
# RunPython operations to refer to the local versions:
# project.drinks.migrations.0005_drinktarget_drink_type

class Migration(migrations.Migration):

    replaces = [
        ('drinks', '0001_initial'),
        ('drinks', '0002_auto_20191118_2203'),
        ('drinks', '0003_auto_20200723_1000'),
        ('drinks', '0004_alter_drinktarget_quantity'),
        ('drinks', '0005_drinktarget_drink_type')
    ]

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('counters', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Drink',
            fields=[],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('counters.counter',),
        ),
        migrations.CreateModel(
            name='DrinkTarget',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1974), django.core.validators.MaxValueValidator(2050)])),
                ('quantity', models.FloatField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='drink_targets', to=settings.AUTH_USER_MODEL)),
                ('drink_type', models.CharField(choices=[('beer', 'Beer'), ('wine', 'Wine'), ('vodka', 'Vodka'), ('stdav', 'Std Av')], default='beer', max_length=7)),
            ],
            options={
                'ordering': ['-year'],
                'unique_together': {('year', 'user')},
            },
        ),
        migrations.RunPython(convert_beer_to_av)
    ]
