# Generated by Django 4.1.7 on 2023-02-21 20:14

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("savings", "0006_savingbalance_sold_savingbalance_sold_fee"),
    ]

    operations = [
        migrations.AlterField(
            model_name="saving",
            name="fee",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="saving",
            name="price",
            field=models.PositiveIntegerField(
                validators=[django.core.validators.MinValueValidator(1)]
            ),
        ),
        migrations.AlterField(
            model_name="savingbalance",
            name="fee",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="savingbalance",
            name="incomes",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="savingbalance",
            name="invested",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="savingbalance",
            name="market_value",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="savingbalance",
            name="past_amount",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="savingbalance",
            name="past_fee",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="savingbalance",
            name="per_year_fee",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="savingbalance",
            name="per_year_incomes",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="savingbalance",
            name="profit_proc",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="savingbalance",
            name="profit_sum",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="savingbalance",
            name="sold",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="savingbalance",
            name="sold_fee",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
