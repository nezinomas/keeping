# Generated by Django 3.2 on 2021-09-03 17:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('debts', '0008_auto_20210827_1414'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='borrowreturn',
            options={'ordering': ['borrow__closed', 'borrow__name', '-date']},
        ),
        migrations.AlterModelOptions(
            name='lentreturn',
            options={'ordering': ['lent__closed', 'lent__name', '-date']},
        ),
    ]
