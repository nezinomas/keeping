from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from ..accounts import models as account
from ..core.services.signals_service import journal_user
from ..debts import models as debt
from ..debts.services.model_services import DebtModelService
from ..expenses import models as expense
from ..incomes import models as income
from ..pensions import models as pension
from ..savings import models as saving
from ..transactions import models as transaction
from ..transactions.services.close_year import FundCloseYear
from ..users.models import User
from . import balance_sources
from . import models as bookkeeping

# each sender is named once per signal: its receiver lists every sync, in order


@receiver(post_delete, sender=income.Income)
@receiver(post_delete, sender=expense.Expense)
@receiver(post_save, sender=transaction.Transaction)
@receiver(post_delete, sender=transaction.Transaction)
@receiver(post_save, sender=debt.Debt)
@receiver(post_delete, sender=debt.Debt)
@receiver(post_save, sender=bookkeeping.AccountWorth)
# closing an account drops its later years
@receiver(post_save, sender=account.Account)
def accounts_signal(sender: object, instance: models.Model, **kwargs):
    balance_sources.sync_accounts(journal_user(instance))


@receiver(post_save, sender=income.Income)
@receiver(post_save, sender=expense.Expense)
def entry_saved_signal(
    sender: object, instance: income.Income | expense.Expense, **kwargs
):
    balance_sources.sync_accounts(journal_user(instance))
    _lower_first_record(instance)


def _lower_first_record(instance: income.Income | expense.Expense) -> None:
    journal = instance.journal
    if journal.first_record > instance.date:
        journal.first_record = instance.date
        journal.save(update_fields=["first_record"])


@receiver(post_save, sender=debt.DebtReturn)
def debt_return_saved_signal(sender: object, instance: debt.DebtReturn, **kwargs):
    _sync_debt_return(instance)


@receiver(post_delete, sender=debt.DebtReturn)
def debt_return_deleted_signal(
    sender: object, instance: debt.DebtReturn, origin: models.Model, **kwargs
):
    # deleting a Debt syncs the accounts once itself, whatever number of returns go
    if isinstance(origin, debt.Debt):
        return

    _sync_debt_return(instance)


def _sync_debt_return(instance: debt.DebtReturn) -> None:
    balance_sources.sync_accounts(journal_user(instance))
    # every debt of the type: a return moved to another debt changes the one it left
    DebtModelService.sync_returned(
        instance.debt.journal_id, debt.Debt.DebtType(instance.debt.debt_type)
    )


@receiver(post_save, sender=saving.Saving)
@receiver(post_delete, sender=saving.Saving)
# A type's fee source and close year change its balances.
@receiver(post_save, sender=saving.SavingType)
def saving_signal(sender: object, instance: models.Model, **kwargs):
    user = journal_user(instance)
    balance_sources.sync_accounts(user)
    balance_sources.sync_savings(user)


@receiver(post_save, sender=bookkeeping.SavingWorth)
def savings_signal(sender: object, instance: models.Model, **kwargs):
    balance_sources.sync_savings(journal_user(instance))


@receiver(post_save, sender=transaction.SavingClose)
def sell_saved_signal(sender: object, instance: transaction.SavingClose, **kwargs):
    user = journal_user(instance)
    balance_sources.sync_accounts(user)
    _move_saved(instance, user)


@receiver(post_delete, sender=transaction.SavingClose)
def sell_deleted_signal(sender: object, instance: transaction.SavingClose, **kwargs):
    user = journal_user(instance)
    balance_sources.sync_accounts(user)
    _move_deleted(instance, user)


@receiver(post_save, sender=transaction.SavingChange)
def switch_saved_signal(sender: object, instance: transaction.SavingChange, **kwargs):
    _move_saved(instance, journal_user(instance))


@receiver(post_delete, sender=transaction.SavingChange)
def switch_deleted_signal(sender: object, instance: transaction.SavingChange, **kwargs):
    _move_deleted(instance, journal_user(instance))


def _move_saved(instance: transaction.FundMove, user: User) -> None:
    # the close year first: the savings sync reads it
    FundCloseYear.follow(instance.from_account_id, instance.close_rule)
    FundCloseYear.follow_removed(instance.left_funds)
    instance.settle()

    balance_sources.sync_savings(user)


def _move_deleted(instance: transaction.FundMove, user: User) -> None:
    FundCloseYear.follow_removed(instance.removed)

    balance_sources.sync_savings(user)


@receiver(post_save, sender=pension.Pension)
@receiver(post_delete, sender=pension.Pension)
@receiver(post_save, sender=bookkeeping.PensionWorth)
# Closing a type drops its later rows, so the sync runs on the type itself.
@receiver(post_save, sender=pension.PensionType)
def pensions_signal(sender: object, instance: models.Model, **kwargs):
    balance_sources.sync_pensions(journal_user(instance))
