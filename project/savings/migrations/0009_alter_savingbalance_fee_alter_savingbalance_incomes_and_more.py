# Generated by Django 4.1.7 on 2023-02-22 08:23

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("savings", "0008_alter_savingbalance_profit_proc"),
    ]

    operations = [
        migrations.AlterField(
            model_name="savingbalance",
            name="fee",
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="savingbalance",
            name="incomes",
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="savingbalance",
            name="invested",
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="savingbalance",
            name="market_value",
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="savingbalance",
            name="past_amount",
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="savingbalance",
            name="past_fee",
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="savingbalance",
            name="per_year_fee",
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="savingbalance",
            name="per_year_incomes",
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="savingbalance",
            name="profit_sum",
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="savingbalance",
            name="sold",
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="savingbalance",
            name="sold_fee",
            field=models.IntegerField(default=0),
        ),
    ]
