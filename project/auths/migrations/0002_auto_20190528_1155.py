# Generated by Django 2.2.1 on 2019-05-28 08:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auths', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='month',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='year',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
