# Generated by Django 4.1.4 on 2022-12-09 13:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pensions', '0002_pensionbalance_latest_check'),
    ]

    operations = [
        migrations.AddField(
            model_name='pensionbalance',
            name='per_year_fee',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='pensionbalance',
            name='per_year_incomes',
            field=models.FloatField(default=0.0),
        ),
    ]
