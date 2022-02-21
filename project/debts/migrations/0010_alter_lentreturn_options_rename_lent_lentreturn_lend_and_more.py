# Generated by Django 4.0.1 on 2022-02-11 18:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_account_created'),
        ('debts', '0009_auto_20210903_2053'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Lent',
            new_name='Debt',
        ),
        migrations.RenameModel(
            old_name='LentReturn',
            new_name='DebtReturn',
        ),
        migrations.AlterModelOptions(
            name='debtreturn',
            options={'ordering': ['debt__closed', 'debt__name', '-date']},
        ),
        migrations.RenameField(
            model_name='debtreturn',
            old_name='lent',
            new_name='debt',
        ),
        migrations.AlterField(
            model_name='debt',
            name='account',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='debt_from_account', to='accounts.account'),
        ),
        migrations.AlterField(
            model_name='debtreturn',
            name='account',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='debt_return_account', to='accounts.account'),
        ),
    ]
