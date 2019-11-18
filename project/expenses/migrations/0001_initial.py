# Generated by Django 2.2.6 on 2019-11-18 20:03

from decimal import Decimal
import django.core.validators
from django.db import migrations, models
import django.db.models.expressions


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Expense',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=8, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('quantity', models.IntegerField(default=1)),
                ('remark', models.TextField(blank=True, max_length=1000)),
                ('exception', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['-date', 'expense_type', django.db.models.expressions.OrderBy(django.db.models.expressions.F('expense_name')), 'price'],
            },
        ),
        migrations.CreateModel(
            name='ExpenseName',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(editable=False, max_length=254)),
                ('title', models.CharField(max_length=254, validators=[django.core.validators.MinLengthValidator(3)])),
                ('valid_for', models.PositiveIntegerField(blank=True, null=True)),
            ],
            options={
                'ordering': [django.db.models.expressions.OrderBy(django.db.models.expressions.F('valid_for'), descending=True, nulls_first=True), 'title'],
            },
        ),
        migrations.CreateModel(
            name='ExpenseType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=254, unique=True, validators=[django.core.validators.MinLengthValidator(3)])),
                ('slug', models.SlugField(editable=False, max_length=254)),
                ('necessary', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['title'],
            },
        ),
    ]
