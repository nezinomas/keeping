# Generated by Django 2.2.6 on 2019-10-18 14:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('savings', '0005_auto_20191012_2054'),
    ]

    operations = [
        migrations.AddField(
            model_name='savingtype',
            name='closed',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
