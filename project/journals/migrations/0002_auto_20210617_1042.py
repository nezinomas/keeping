# Generated by Django 3.2.3 on 2021-06-17 07:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('journals', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='journal',
            name='month',
        ),
        migrations.RemoveField(
            model_name='journal',
            name='year',
        ),
    ]
