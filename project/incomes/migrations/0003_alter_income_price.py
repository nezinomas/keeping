# Generated by Django 4.1.7 on 2023-02-24 07:55

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("incomes", "0002_alter_income_price"),
    ]

    operations = [
        migrations.AlterField(
            model_name="income",
            name="price",
            field=models.PositiveIntegerField(),
        ),
    ]
