# Generated by Django 4.0.4 on 2022-05-19 13:41

from decimal import Decimal
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
        ('journals', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='IncomeType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=25, validators=[django.core.validators.MinLengthValidator(3)])),
                ('slug', models.SlugField(editable=False, max_length=25)),
                ('type', models.CharField(choices=[('salary', 'Salary'), ('dividents', 'Dividents'), ('other', 'Other')], default='salary', max_length=12)),
                ('journal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='income_types', to='journals.journal')),
            ],
            options={
                'ordering': ['title'],
                'unique_together': {('journal', 'title')},
            },
        ),
        migrations.CreateModel(
            name='Income',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=8, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('remark', models.TextField(blank=True, max_length=1000)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='incomes', to='accounts.account')),
                ('income_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='incomes.incometype')),
            ],
        ),
        migrations.AddIndex(
            model_name='income',
            index=models.Index(fields=['account', 'income_type'], name='incomes_inc_account_90c123_idx'),
        ),
        migrations.AddIndex(
            model_name='income',
            index=models.Index(fields=['income_type'], name='incomes_inc_income__b6fb65_idx'),
        ),
    ]
