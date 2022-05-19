# Generated by Django 4.0.4 on 2022-05-19 13:41

from decimal import Decimal
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('pensions', '0001_initial'),
        ('accounts', '0001_initial'),
        ('savings', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SavingWorth',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=8, validators=[django.core.validators.MinValueValidator(Decimal('0.0'))])),
                ('saving_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='savings_worth', to='savings.savingtype')),
            ],
            options={
                'ordering': ['-date'],
                'get_latest_by': ['date'],
            },
        ),
        migrations.CreateModel(
            name='PensionWorth',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=8, validators=[django.core.validators.MinValueValidator(Decimal('0.0'))])),
                ('pension_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pensions_worth', to='pensions.pensiontype')),
            ],
            options={
                'ordering': ['-date'],
                'get_latest_by': ['date'],
            },
        ),
        migrations.CreateModel(
            name='AccountWorth',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=8, validators=[django.core.validators.MinValueValidator(Decimal('0.0'))])),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accounts_worth', to='accounts.account')),
            ],
            options={
                'ordering': ['-date'],
                'get_latest_by': ['date'],
            },
        ),
    ]