# Generated by Django 3.2.3 on 2021-06-09 05:56

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0003_booktarget'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='title',
            field=models.CharField(max_length=254, validators=[django.core.validators.MinLengthValidator(2)]),
        ),
    ]