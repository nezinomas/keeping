# Generated by Django 4.0.1 on 2022-02-13 15:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('debts', '0010_alter_lentreturn_options_rename_lent_lentreturn_lend_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='borrowreturn',
            name='account',
        ),
        migrations.RemoveField(
            model_name='borrowreturn',
            name='borrow',
        ),
        migrations.DeleteModel(
            name='Borrow',
        ),
        migrations.DeleteModel(
            name='BorrowReturn',
        ),
    ]
