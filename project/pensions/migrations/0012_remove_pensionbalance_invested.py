# Generated by Django 5.0.1 on 2024-02-02 12:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("pensions", "0011_remove_pensionbalance_profit_proc"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="pensionbalance",
            name="invested",
        ),
    ]