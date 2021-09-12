# Generated by Django 2.2.6 on 2019-11-18 20:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('pensions', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='pensiontype',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pension_types', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='pensionbalance',
            name='pension_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pensions_balance', to='pensions.PensionType'),
        ),
        migrations.AddField(
            model_name='pension',
            name='pension_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pensions.PensionType'),
        ),
    ]
