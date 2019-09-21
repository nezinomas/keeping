# Generated by Django 2.2.1 on 2019-05-22 11:58

from django.db import migrations
import django.db.models.expressions


class Migration(migrations.Migration):

    dependencies = [
        ('expenses', '0015_expensename_valid_for'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='expense',
            options={'ordering': ['-date', 'expense_type', django.db.models.expressions.OrderBy(django.db.models.expressions.F('expense_name')), 'price']},
        ),
        migrations.AlterModelOptions(
            name='expensename',
            options={'ordering': [django.db.models.expressions.OrderBy(django.db.models.expressions.F('valid_for'), descending=True, nulls_first=True), 'title']},
        ),
    ]
