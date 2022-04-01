# Generated by Django 4.0.3 on 2022-03-18 10:06

from decimal import Decimal
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    replaces = [('savings', '0001_initial'), ('savings', '0002_auto_20191118_2203'), ('savings', '0003_auto_20200123_1305'), ('savings', '0004_auto_20210623_1542'), ('savings', '0005_savingtype_type'), ('savings', '0006_alter_savingtype_options'), ('savings', '0007_auto_20210805_1008'), ('savings', '0008_savingtype_created'), ('savings', '0009_rename_fees_savingbalance_fee')]

    initial = True

    dependencies = [
        ('journals', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0002_account_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='SavingType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=254, unique=True, validators=[django.core.validators.MinLengthValidator(3)])),
                ('slug', models.SlugField(editable=False, max_length=254)),
                ('closed', models.PositiveIntegerField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saving_types', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['title'],
            },
        ),
        migrations.CreateModel(
            name='SavingBalance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1974), django.core.validators.MaxValueValidator(2050)])),
                ('past_amount', models.FloatField(default=0.0)),
                ('past_fee', models.FloatField(default=0.0)),
                ('fees', models.FloatField(default=0.0)),
                ('invested', models.FloatField(default=0.0)),
                ('incomes', models.FloatField(default=0.0)),
                ('market_value', models.FloatField(default=0.0)),
                ('profit_incomes_proc', models.FloatField(default=0.0)),
                ('profit_incomes_sum', models.FloatField(default=0.0)),
                ('profit_invested_proc', models.FloatField(default=0.0)),
                ('profit_invested_sum', models.FloatField(default=0.0)),
                ('saving_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='savings_balance', to='savings.savingtype')),
            ],
        ),
        migrations.CreateModel(
            name='Saving',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=8, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('fee', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('remark', models.TextField(blank=True, max_length=1000)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='savings', to='accounts.account')),
                ('saving_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='savings.savingtype')),
            ],
            options={
                'ordering': ['-date', 'saving_type'],
            },
        ),
        migrations.AddIndex(
            model_name='saving',
            index=models.Index(fields=['account', 'saving_type'], name='savings_sav_account_119c89_idx'),
        ),
        migrations.AddIndex(
            model_name='saving',
            index=models.Index(fields=['saving_type'], name='savings_sav_saving__07f3d9_idx'),
        ),
        migrations.AlterField(
            model_name='savingtype',
            name='title',
            field=models.CharField(max_length=254, validators=[django.core.validators.MinLengthValidator(3)]),
        ),
        migrations.AlterUniqueTogether(
            name='savingtype',
            unique_together={('user', 'title')},
        ),
        migrations.AddField(
            model_name='savingtype',
            name='journal',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='saving_types', to='journals.journal'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='savingtype',
            unique_together={('journal', 'title')},
        ),
        migrations.RemoveField(
            model_name='savingtype',
            name='user',
        ),
        migrations.AddField(
            model_name='savingtype',
            name='type',
            field=models.CharField(choices=[('shares', 'Shares'), ('funds', 'Funds'), ('pensions', 'Pensions')], default='funds', max_length=12),
        ),
        migrations.AlterModelOptions(
            name='savingtype',
            options={'ordering': ['type', 'title']},
        ),
        migrations.AlterField(
            model_name='savingtype',
            name='slug',
            field=models.SlugField(editable=False, max_length=25),
        ),
        migrations.AlterField(
            model_name='savingtype',
            name='title',
            field=models.CharField(max_length=25, validators=[django.core.validators.MinLengthValidator(3)]),
        ),
        migrations.AddField(
            model_name='savingtype',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.RenameField(
            model_name='savingbalance',
            old_name='fees',
            new_name='fee',
        ),
    ]