# Generated by Django 4.1.4 on 2022-12-14 14:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('savings', '0004_remove_savingbalance_profit_incomes_proc_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='savingbalance',
            old_name='profit_invested_proc',
            new_name='profit_proc',
        ),
        migrations.RenameField(
            model_name='savingbalance',
            old_name='profit_invested_sum',
            new_name='profit_sum',
        ),
    ]
