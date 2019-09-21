# Generated by Django 2.2.1 on 2019-05-27 10:22

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='author',
            field=models.CharField(max_length=254, validators=[django.core.validators.MinLengthValidator(3)]),
        ),
        migrations.AlterField(
            model_name='book',
            name='title',
            field=models.CharField(max_length=254, validators=[django.core.validators.MinLengthValidator(3)]),
        ),
    ]
