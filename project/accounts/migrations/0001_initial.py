# Generated by Django 4.0.4 on 2022-05-19 13:41

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('journals', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=25, validators=[django.core.validators.MinLengthValidator(3)])),
                ('slug', models.SlugField(editable=False, max_length=25)),
                ('order', models.PositiveIntegerField(default=10)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('closed', models.PositiveIntegerField(blank=True, null=True)),
                ('journal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accounts', to='journals.journal')),
            ],
            options={
                'ordering': ['order', 'title'],
                'unique_together': {('journal', 'title')},
            },
        ),
        migrations.CreateModel(
            name='AccountBalance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1974), django.core.validators.MaxValueValidator(2050)])),
                ('past', models.FloatField(default=0.0)),
                ('incomes', models.FloatField(default=0.0)),
                ('expenses', models.FloatField(default=0.0)),
                ('balance', models.FloatField(default=0.0)),
                ('have', models.FloatField(default=0.0)),
                ('delta', models.FloatField(default=0.0)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accounts_balance', to='accounts.account')),
            ],
        ),
    ]
