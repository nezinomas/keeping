# Generated by Django 4.0.4 on 2022-05-19 13:41

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('started', models.DateField()),
                ('ended', models.DateField(blank=True, null=True)),
                ('author', models.CharField(max_length=254, validators=[django.core.validators.MinLengthValidator(3)])),
                ('title', models.CharField(max_length=254, validators=[django.core.validators.MinLengthValidator(2)])),
                ('remark', models.TextField(blank=True, max_length=200)),
            ],
            options={
                'ordering': ['-started', 'author'],
            },
        ),
        migrations.CreateModel(
            name='BookTarget',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1974), django.core.validators.MaxValueValidator(2050)])),
                ('quantity', models.PositiveIntegerField()),
            ],
            options={
                'ordering': ['-year'],
            },
        ),
    ]