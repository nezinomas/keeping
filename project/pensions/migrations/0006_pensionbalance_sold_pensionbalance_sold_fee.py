# Generated by Django 4.1.4 on 2022-12-15 13:52

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "pensions",
            "0005_rename_profit_invested_proc_pensionbalance_profit_proc_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="pensionbalance",
            name="sold",
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name="pensionbalance",
            name="sold_fee",
            field=models.FloatField(default=0.0),
        ),
    ]
