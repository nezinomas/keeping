# Generated by Django 3.0.2 on 2020-02-24 12:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pensions', '0004_pension_fee'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pension',
            name='price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True),
        ),
    ]
