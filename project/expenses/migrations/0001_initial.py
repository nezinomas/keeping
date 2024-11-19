# Generated by Django 4.0.4 on 2022-05-19 13:41

from decimal import Decimal

import django.core.validators
import django.db.models.deletion
import django.db.models.expressions
from django.db import migrations, models

import project.expenses.helpers.models_helper


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
        ('journals', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExpenseType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=25, validators=[django.core.validators.MinLengthValidator(3)])),
                ('slug', models.SlugField(editable=False, max_length=25)),
                ('necessary', models.BooleanField(default=False)),
                ('journal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='expense_types', to='journals.journal')),
            ],
            options={
                'ordering': ['title'],
                'unique_together': {('journal', 'title')},
            },
        ),
        migrations.CreateModel(
            name='ExpenseName',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(editable=False, max_length=25)),
                ('title', models.CharField(max_length=254, validators=[django.core.validators.MinLengthValidator(3)])),
                ('valid_for', models.PositiveIntegerField(blank=True, null=True)),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='expenses.expensetype')),
            ],
            options={
                'ordering': [django.db.models.expressions.OrderBy(django.db.models.expressions.F('valid_for'), descending=True, nulls_first=True), 'title'],
                'unique_together': {('title', 'parent')},
            },
        ),
        migrations.CreateModel(
            name='Expense',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=8, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('quantity', models.IntegerField(default=1)),
                ('remark', models.TextField(blank=True, max_length=1000)),
                ('exception', models.BooleanField(default=False)),
                ('attachment', models.ImageField(blank=True, upload_to=project.expenses.helpers.models_helper.upload_attachment)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='expenses', to='accounts.account')),
                ('expense_name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='expenses.expensename')),
                ('expense_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='expenses.expensetype')),
            ],
        ),
        migrations.AddIndex(
            model_name='expense',
            index=models.Index(fields=['date'], name='expenses_ex_date_17a2b2_idx'),
        ),
        migrations.AddIndex(
            model_name='expense',
            index=models.Index(fields=['expense_type'], name='expenses_ex_expense_3c4432_idx'),
        ),
        migrations.AddIndex(
            model_name='expense',
            index=models.Index(fields=['expense_name'], name='expenses_ex_expense_bfb2f7_idx'),
        ),
    ]
