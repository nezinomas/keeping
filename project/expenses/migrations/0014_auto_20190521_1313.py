# Generated by Django 2.2.1 on 2019-05-21 10:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expenses', '0013_auto_20190517_1015'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expensename',
            name='slug',
            field=models.SlugField(editable=False, max_length=254),
        ),
        migrations.AlterField(
            model_name='expensetype',
            name='slug',
            field=models.SlugField(editable=False, max_length=254),
        ),
    ]
