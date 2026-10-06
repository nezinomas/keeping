from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from ..bookkeeping import models as bookkeeping
from ..debts import models as debt
from ..expenses import models as expense
from ..incomes import models as income
from ..pensions import models as pension
from ..savings import models as saving
from ..transactions import models as transaction
from ..transactions.services.close_year import FundCloseYear
from .services import signals_service


# Accounts Signals
@receiver(post_save, sender=income.Income)
@receiver(post_delete, sender=income.Income)
@receiver(post_save, sender=expense.Expense)
@receiver(post_delete, sender=expense.Expense)
@receiver(post_save, sender=saving.Saving)
@receiver(post_delete, sender=saving.Saving)
@receiver(post_save, sender=transaction.Transaction)
@receiver(post_delete, sender=transaction.Transaction)
@receiver(post_save, sender=transaction.SavingClose)
@receiver(post_delete, sender=transaction.SavingClose)
@receiver(post_save, sender=debt.Debt)
@receiver(post_delete, sender=debt.Debt)
@receiver(post_save, sender=debt.DebtReturn)
@receiver(post_delete, sender=debt.DebtReturn)
@receiver(post_save, sender=bookkeeping.AccountWorth)
def accounts_signal(sender: object, instance: models.Model, *args, **kwargs):
    signals_service.sync_accounts(signals_service.journal_user(instance))


# A type's fee source and close year change its balances.
@receiver(post_save, sender=saving.SavingType)
def saving_type_signal(sender: object, instance: saving.SavingType, *args, **kwargs):
    user = signals_service.journal_user(instance)
    signals_service.sync_accounts(user)
    signals_service.sync_savings(user)


# Savings Signals
@receiver(post_save, sender=saving.Saving)
@receiver(post_delete, sender=saving.Saving)
@receiver(post_save, sender=bookkeeping.SavingWorth)
def savings_signal(sender: object, instance: models.Model, *args, **kwargs):
    signals_service.sync_savings(signals_service.journal_user(instance))


@receiver(post_save, sender=transaction.SavingClose)
@receiver(post_delete, sender=transaction.SavingClose)
@receiver(post_save, sender=transaction.SavingChange)
@receiver(post_delete, sender=transaction.SavingChange)
def move_signal(sender: object, instance: models.Model, *args, **kwargs):
    # the close year first: the savings sync reads it
    FundCloseYear.follow(instance.from_account_id, instance.close_rule)
    for fund_pk in instance.left_funds:
        FundCloseYear.follow(fund_pk)
    instance.settle()

    signals_service.sync_savings(signals_service.journal_user(instance))


# Pensions Signals
@receiver(post_save, sender=pension.Pension)
@receiver(post_delete, sender=pension.Pension)
@receiver(post_save, sender=bookkeeping.PensionWorth)
def pensions_signal(sender: object, instance: models.Model, *args, **kwargs):
    signals_service.sync_pensions(signals_service.journal_user(instance))


# Closing a type drops its later rows, so the sync runs on the type itself.
@receiver(post_save, sender=pension.PensionType)
def pension_type_signal(sender: object, instance: pension.PensionType, *args, **kwargs):
    signals_service.sync_pensions(signals_service.journal_user(instance))


# Update Journal first_record field
@receiver(post_save, sender=income.Income)
@receiver(post_save, sender=expense.Expense)
def update_journal_first_record(sender, instance, created, **kwargs):
    journal = instance.account.journal

    if journal.first_record > instance.date:
        journal.first_record = instance.date
        journal.save(update_fields=["first_record"])
