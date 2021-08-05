# Generated by Django 3.2.5 on 2021-08-05 07:08

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('incomes', '0006_incometype_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='incometype',
            name='slug',
            field=models.SlugField(editable=False, max_length=25),
        ),
        migrations.AlterField(
            model_name='incometype',
            name='title',
            field=models.CharField(max_length=25, validators=[django.core.validators.MinLengthValidator(3)]),
        ),
    ]
