# Generated by Django 2.2 on 2019-05-16 18:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expenses', '0008_auto_20190516_2044'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expensename',
            name='title',
            field=models.CharField(max_length=254, unique=True),
        ),
        migrations.AlterField(
            model_name='expensesubname',
            name='title',
            field=models.CharField(max_length=254),
        ),
    ]
