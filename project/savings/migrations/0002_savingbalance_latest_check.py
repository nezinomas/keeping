# Generated by Django 4.1.3 on 2022-12-07 07:50

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("savings", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="savingbalance",
            name="latest_check",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
