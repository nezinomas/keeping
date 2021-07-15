# Generated by Django 3.2.3 on 2021-06-23 12:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_auto_20210623_1542'),
        ('transactions', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='from_account',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions_from', to='accounts.account'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='to_account',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions_to', to='accounts.account'),
        ),
    ]
