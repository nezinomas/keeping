# Generated by Django 3.2.6 on 2021-08-27 11:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('debts', '0007_auto_20210623_1542'),
    ]

    operations = [
        migrations.AlterField(
            model_name='borrowreturn',
            name='date',
            field=models.DateField(),
        ),
        migrations.AlterField(
            model_name='lentreturn',
            name='date',
            field=models.DateField(),
        ),
    ]
