# Generated by Django 4.0.1 on 2022-02-20 11:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('debts', '0012_debt_type'),
    ]

    operations = [
        migrations.RenameField(
            model_name='debt',
            old_name='type',
            new_name='debt_type',
        ),
    ]