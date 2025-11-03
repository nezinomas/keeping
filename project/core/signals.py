from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from ..accounts import models as account
from ..bookkeeping import models as bookkeeping
from ..debts import models as debt
from ..expenses import models as expense
from ..incomes import models as income
from ..pensions import models as pension
from ..savings import models as saving
from ..transactions import models as transaction
from .lib.signals import Accounts, GetData, Savings, SignalBase


# -------------------------------------------------------------------------------------
#                                                                      Accounts Signals
# -------------------------------------------------------------------------------------
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
def accounts_signal(sender: object, instance: object, *args, **kwargs):
    data = accounts_data()
    BalanceSynchronizer(account.AccountBalance, data.df)


def accounts_data() -> SignalBase:
    conf = {
        "incomes": (
            income.Income,
            debt.Debt,
            debt.DebtReturn,
            transaction.Transaction,
            transaction.SavingClose,
        ),
        "expenses": (
            expense.Expense,
            debt.Debt,
            debt.DebtReturn,
            transaction.Transaction,
            saving.Saving,
        ),
        "have": (bookkeeping.AccountWorth,),
        "types": (account.Account,),
    }
    return Accounts(GetData(conf))


# -------------------------------------------------------------------------------------
#                                                                       Savings Signals
# -------------------------------------------------------------------------------------
@receiver(post_save, sender=saving.Saving)
@receiver(post_delete, sender=saving.Saving)
@receiver(post_save, sender=transaction.SavingClose)
@receiver(post_delete, sender=transaction.SavingClose)
@receiver(post_save, sender=transaction.SavingChange)
@receiver(post_delete, sender=transaction.SavingChange)
@receiver(post_save, sender=bookkeeping.SavingWorth)
def savings_signal(sender: object, instance: object, *args, **kwargs):
    data = savings_data()
    BalanceSynchronizer(saving.SavingBalance, data.df)


def savings_data() -> SignalBase:
    conf = {
        "incomes": (
            saving.Saving,
            transaction.SavingChange,
        ),
        "expenses": (
            transaction.SavingClose,
            transaction.SavingChange,
        ),
        "have": (bookkeeping.SavingWorth,),
        "types": (saving.SavingType,),
    }
    return Savings(GetData(conf))


# -------------------------------------------------------------------------------------
#                                                                      Pensions Signals
# -------------------------------------------------------------------------------------
@receiver(post_save, sender=pension.Pension)
@receiver(post_delete, sender=pension.Pension)
@receiver(post_save, sender=bookkeeping.PensionWorth)
def pensions_signal(sender: object, instance: object, *args, **kwargs):
    data = pensions_data()
    BalanceSynchronizer(pension.PensionBalance, data.df)


def pensions_data() -> SignalBase:
    conf = {
        "incomes": (pension.Pension,),
        "have": (bookkeeping.PensionWorth,),
        "types": (pension.PensionType,),
    }
    return Savings(GetData(conf))
