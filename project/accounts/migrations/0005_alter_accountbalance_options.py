# Generated by Django 5.2 on 2025-05-05 13:18

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_alter_accountbalance_balance_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="accountbalance",
            options={"ordering": ["year", "account__pk"]},
        ),
    ]
