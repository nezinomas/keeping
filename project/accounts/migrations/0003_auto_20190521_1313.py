# Generated by Django 2.2.1 on 2019-05-21 10:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auto_20190516_2101'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='slug',
            field=models.SlugField(editable=False, max_length=254),
        ),
    ]
