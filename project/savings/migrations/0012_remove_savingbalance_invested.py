# Generated by Django 5.0.1 on 2024-02-02 12:52

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("savings", "0011_remove_savingbalance_profit_proc"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="savingbalance",
            name="invested",
        ),
    ]
