# Generated by Django 2.2.6 on 2019-11-18 20:03

from decimal import Decimal
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0002_account_user'),
        ('savings', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=8, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('from_account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='transactions_from', to='accounts.Account')),
                ('to_account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='transactions_to', to='accounts.Account')),
            ],
            options={
                'ordering': ['-date', 'price', 'from_account'],
            },
        ),
        migrations.CreateModel(
            name='SavingClose',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('fee', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('price', models.DecimalField(decimal_places=2, max_digits=8, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('from_account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='savings_close_from', to='savings.SavingType')),
                ('to_account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='savings_close_to', to='accounts.Account')),
            ],
            options={
                'ordering': ['-date', 'price', 'from_account'],
            },
        ),
        migrations.CreateModel(
            name='SavingChange',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('fee', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('price', models.DecimalField(decimal_places=2, max_digits=8, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('from_account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='savings_change_from', to='savings.SavingType')),
                ('to_account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='savings_change_to', to='savings.SavingType')),
            ],
            options={
                'ordering': ['-date', 'price', 'from_account'],
            },
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['from_account'], name='transaction_from_ac_ad7a61_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['to_account'], name='transaction_to_acco_70c2d0_idx'),
        ),
        migrations.AddIndex(
            model_name='savingclose',
            index=models.Index(fields=['from_account'], name='transaction_from_ac_39cba3_idx'),
        ),
        migrations.AddIndex(
            model_name='savingclose',
            index=models.Index(fields=['to_account'], name='transaction_to_acco_eda711_idx'),
        ),
        migrations.AddIndex(
            model_name='savingchange',
            index=models.Index(fields=['from_account'], name='transaction_from_ac_366d46_idx'),
        ),
        migrations.AddIndex(
            model_name='savingchange',
            index=models.Index(fields=['to_account'], name='transaction_to_acco_19d2c1_idx'),
        ),
    ]
