# Generated by Django 4.0.4 on 2022-04-28 08:00

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


def copy_data_from_counters(apps, schema_editor):
    Counter = apps.get_model('counters', 'Counter')
    counter = Counter.objects.filter(counter_type='drinks')
    Drink = apps.get_model('drinks', 'Drink')

    for i in counter:
        Drink.objects.create(user=i.user, quantity=i.quantity,
                             date=i.date, option=i.option)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('drinks', '0001_squashed_0005_drinktarget_drink_type'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Drink',
        ),
        migrations.CreateModel(
            name='Drink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('quantity', models.FloatField(validators=[django.core.validators.MinValueValidator(0.1)])),
                ('option', models.CharField(choices=[('beer', 'Beer'), ('wine', 'Wine'), ('vodka', 'Vodka'), ('stdav', 'Std Av')], default='beer', max_length=7)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RunPython(copy_data_from_counters)
    ]
