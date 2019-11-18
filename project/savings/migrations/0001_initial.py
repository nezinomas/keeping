# Generated by Django 2.2.6 on 2019-11-18 20:03

from decimal import Decimal
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Saving',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=8, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('fee', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('remark', models.TextField(blank=True, max_length=1000)),
            ],
            options={
                'ordering': ['-date', 'saving_type'],
            },
        ),
        migrations.CreateModel(
            name='SavingBalance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1974), django.core.validators.MaxValueValidator(2050)])),
                ('past_amount', models.FloatField(default=0.0)),
                ('past_fee', models.FloatField(default=0.0)),
                ('fees', models.FloatField(default=0.0)),
                ('invested', models.FloatField(default=0.0)),
                ('incomes', models.FloatField(default=0.0)),
                ('market_value', models.FloatField(default=0.0)),
                ('profit_incomes_proc', models.FloatField(default=0.0)),
                ('profit_incomes_sum', models.FloatField(default=0.0)),
                ('profit_invested_proc', models.FloatField(default=0.0)),
                ('profit_invested_sum', models.FloatField(default=0.0)),
            ],
        ),
        migrations.CreateModel(
            name='SavingType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=254, unique=True, validators=[django.core.validators.MinLengthValidator(3)])),
                ('slug', models.SlugField(editable=False, max_length=254)),
                ('closed', models.PositiveIntegerField(blank=True, null=True)),
            ],
            options={
                'ordering': ['title'],
            },
        ),
    ]
