# Generated by Django 5.1.4 on 2025-01-02 14:09

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('savings', '0013_savingbalance_profit_proc'),
    ]

    operations = [
        migrations.AlterField(
            model_name='savingtype',
            name='slug',
            field=models.SlugField(editable=False),
        ),
        migrations.AlterField(
            model_name='savingtype',
            name='title',
            field=models.CharField(max_length=50, validators=[django.core.validators.MinLengthValidator(3)]),
        ),
    ]
