# Generated by Django 4.0.3 on 2022-03-18 10:05

from decimal import Decimal
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.expressions
import project.expenses.helpers.models_helper


class Migration(migrations.Migration):

    replaces = [('expenses', '0001_initial'), ('expenses', '0002_auto_20191118_2203'), ('expenses', '0003_auto_20200123_1305'), ('expenses', '0004_auto_20200323_1338'), ('expenses', '0005_expense_attachment'), ('expenses', '0006_auto_20210129_1947'), ('expenses', '0007_auto_20210623_1542'), ('expenses', '0008_auto_20210805_1008'), ('expenses', '0009_alter_expense_attachment')]

    initial = True

    dependencies = [
        ('accounts', '0002_account_user'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('journals', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExpenseType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=254, unique=True, validators=[django.core.validators.MinLengthValidator(3)])),
                ('slug', models.SlugField(editable=False, max_length=254)),
                ('necessary', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='expense_types', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['title'],
            },
        ),
        migrations.CreateModel(
            name='ExpenseName',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(editable=False, max_length=254)),
                ('title', models.CharField(max_length=254, validators=[django.core.validators.MinLengthValidator(3)])),
                ('valid_for', models.PositiveIntegerField(blank=True, null=True)),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='expenses.expensetype')),
            ],
            options={
                'ordering': [django.db.models.expressions.OrderBy(django.db.models.expressions.F('valid_for'), descending=True, nulls_first=True), 'title'],
                'unique_together': {('title', 'parent')},
            },
        ),
        migrations.CreateModel(
            name='Expense',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=8, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('quantity', models.IntegerField(default=1)),
                ('remark', models.TextField(blank=True, max_length=1000)),
                ('exception', models.BooleanField(default=False)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='expenses', to='accounts.account')),
                ('expense_name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='expenses.expensename')),
                ('expense_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='expenses.expensetype')),
            ],
            options={
                'ordering': ['-date', 'expense_type', django.db.models.expressions.OrderBy(django.db.models.expressions.F('expense_name')), 'price'],
            },
        ),
        migrations.AddIndex(
            model_name='expense',
            index=models.Index(fields=['date'], name='expenses_ex_date_17a2b2_idx'),
        ),
        migrations.AddIndex(
            model_name='expense',
            index=models.Index(fields=['expense_type'], name='expenses_ex_expense_3c4432_idx'),
        ),
        migrations.AddIndex(
            model_name='expense',
            index=models.Index(fields=['expense_name'], name='expenses_ex_expense_bfb2f7_idx'),
        ),
        migrations.AlterField(
            model_name='expensetype',
            name='title',
            field=models.CharField(max_length=254, validators=[django.core.validators.MinLengthValidator(3)]),
        ),
        migrations.AlterUniqueTogether(
            name='expensetype',
            unique_together={('user', 'title')},
        ),
        migrations.AlterModelOptions(
            name='expense',
            options={},
        ),
        migrations.AddField(
            model_name='expensetype',
            name='journal',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='expense_types', to='journals.journal'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='expensetype',
            unique_together={('journal', 'title')},
        ),
        migrations.RemoveField(
            model_name='expensetype',
            name='user',
        ),
        migrations.AlterField(
            model_name='expensename',
            name='slug',
            field=models.SlugField(editable=False, max_length=25),
        ),
        migrations.AlterField(
            model_name='expensetype',
            name='slug',
            field=models.SlugField(editable=False, max_length=25),
        ),
        migrations.AlterField(
            model_name='expensetype',
            name='title',
            field=models.CharField(max_length=25, validators=[django.core.validators.MinLengthValidator(3)]),
        ),
        migrations.AddField(
            model_name='expense',
            name='attachment',
            field=models.ImageField(blank=True, upload_to=project.expenses.helpers.models_helper.upload_attachment),
        ),
    ]
