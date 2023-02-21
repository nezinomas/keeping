# Generated by Django 4.1.7 on 2023-02-21 20:14

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "bookkeeping",
            "0003_alter_accountworth_price_alter_pensionworth_price_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="accountworth",
            name="price",
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                validators=[django.core.validators.MinValueValidator(1)],
            ),
        ),
        migrations.AlterField(
            model_name="pensionworth",
            name="price",
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                validators=[django.core.validators.MinValueValidator(1)],
            ),
        ),
        migrations.AlterField(
            model_name="savingworth",
            name="price",
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                validators=[django.core.validators.MinValueValidator(1)],
            ),
        ),
    ]
