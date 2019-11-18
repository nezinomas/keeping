# Generated by Django 2.2.6 on 2019-11-18 20:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('pensions', '0001_initial'),
        ('accounts', '0002_account_user'),
        ('bookkeeping', '0001_initial'),
        ('savings', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='savingworth',
            name='saving_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='savings_worth', to='savings.SavingType'),
        ),
        migrations.AddField(
            model_name='pensionworth',
            name='pension_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pensions_worth', to='pensions.PensionType'),
        ),
        migrations.AddField(
            model_name='accountworth',
            name='account',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accounts_worth', to='accounts.Account'),
        ),
    ]
