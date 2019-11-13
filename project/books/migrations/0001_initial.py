# Generated by Django 2.2.7 on 2019-11-13 07:54

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
                ('title', models.CharField(max_length=254, validators=[django.core.validators.MinLengthValidator(3)])),
                ('remark', models.TextField(blank=True, max_length=200)),
            ],
            options={
                'ordering': ['-started', 'author'],
            },
        ),
    ]
