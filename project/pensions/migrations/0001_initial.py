# Generated by Django 4.0.4 on 2022-05-19 13:41

from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('journals', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PensionType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=25, validators=[django.core.validators.MinLengthValidator(3)])),
                ('slug', models.SlugField(editable=False, max_length=25)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('journal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pension_types', to='journals.journal')),
            ],
            options={
                'ordering': ['title'],
                'unique_together': {('journal', 'title')},
            },
        ),
        migrations.CreateModel(
            name='PensionBalance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1974), django.core.validators.MaxValueValidator(2050)])),
                ('past_amount', models.FloatField(default=0.0)),
                ('past_fee', models.FloatField(default=0.0)),
                ('fee', models.FloatField(default=0.0)),
                ('invested', models.FloatField(default=0.0)),
                ('incomes', models.FloatField(default=0.0)),
                ('market_value', models.FloatField(default=0.0)),
                ('profit_incomes_proc', models.FloatField(default=0.0)),
                ('profit_incomes_sum', models.FloatField(default=0.0)),
                ('profit_invested_proc', models.FloatField(default=0.0)),
                ('profit_invested_sum', models.FloatField(default=0.0)),
                ('pension_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pensions_balance', to='pensions.pensiontype')),
            ],
        ),
        migrations.CreateModel(
            name='Pension',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('price', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0'))])),
                ('fee', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0'))])),
                ('remark', models.TextField(blank=True, max_length=1000)),
                ('pension_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pensions.pensiontype')),
            ],
            options={
                'ordering': ['-date', 'price'],
            },
        ),
    ]
