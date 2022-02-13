from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from ..accounts import models as account
from ..bookkeeping import models as worth
from ..debts import models as debt
from ..expenses import models as expense
from ..incomes import models as income
from ..pensions import models as pension
from ..savings import models as saving
from ..transactions import models as transaction
from .signals_base import SignalBase


# ----------------------------------------------------------------------------
#                                                               AccountBalance
# ----------------------------------------------------------------------------
@receiver(post_save, sender=income.Income)
@receiver(post_save, sender=expense.Expense)
@receiver(post_save, sender=saving.Saving)
@receiver(post_save, sender=transaction.Transaction)
@receiver(post_save, sender=transaction.SavingClose)
@receiver(post_save, sender=debt.Debt)
@receiver(post_save, sender=debt.DebtReturn)
# @receiver(post_save, sender=worth.AccountWorth)
def accounts_post_save(sender: object, instance: object, *args, **kwargs):
    print(f'\n<< Account post save\n{args=}\n{kwargs=}')
    created = kwargs.get('created')
    SignalBase.accounts(sender, instance, created, 'save')
    print(f'\n>> after Account post save\n{account.AccountBalance.objects.values()}\n')


@receiver(post_delete, sender=income.Income)
@receiver(post_delete, sender=expense.Expense)
@receiver(post_delete, sender=saving.Saving)
@receiver(post_delete, sender=transaction.Transaction)
@receiver(post_delete, sender=transaction.SavingClose)
@receiver(post_delete, sender=debt.Debt)
@receiver(post_delete, sender=debt.DebtReturn)
def accounts_post_delete(sender: object, instance: object, *args, **kwargs):
    print(f'\n<< Accounts post delete {args=}\n{kwargs=}\n')
    created = kwargs.get('created')
    SignalBase.accounts(sender, instance, created, 'delete')
    print(f'\n>> after Account post delete\n{account.AccountBalance.objects.values()}\n')


# ----------------------------------------------------------------------------
#                                                               SavingBalance
# ----------------------------------------------------------------------------
@receiver(post_save, sender=saving.Saving)
@receiver(post_save, sender=transaction.SavingClose)
# @receiver(post_save, sender=transaction.SavingChange)
# @receiver(post_save, sender=worth.SavingWorth)
def savings_post_save(sender: object,
                        instance: object,
                        *args,
                        **kwargs):
    print(f'\n<< Savings post save {args=}\n{kwargs=}\n')
    created = kwargs.get('created')
    SignalBase.savings(sender, instance, created, 'save')
    print(f'\n>> after SAVING post save\n{saving.SavingBalance.objects.values()}\n')



@receiver(post_delete, sender=saving.Saving)
@receiver(post_delete, sender=transaction.SavingClose)
# @receiver(post_delete, sender=transaction.SavingChange)
def savings_post_delete(sender: object,
                        instance: object,
                        *args,
                        **kwargs):
    print(f'\n<< Savings post delete {args=}\n{kwargs=}\n')
    created = kwargs.get('created')
    SignalBase.savings(sender, instance, created, 'delete')
    print(f'\n>> after SAVING post delete\n{saving.SavingBalance.objects.values()}\n')


# ----------------------------------------------------------------------------
#                                                               PensionBalance
# ----------------------------------------------------------------------------
# @receiver(post_save, sender=pension.Pension)
# @receiver(post_save, sender=worth.PensionWorth)
def pensions_post_save(sender: object,
                         instance: object,
                         *args,
                         **kwargs):
    print(f'\n<< pensions post save {args=}\n{kwargs=}\n')
    created = kwargs.get('created')
    SignalBase.pensions(sender, instance, created, 'save')


# @receiver(post_save, sender=pension.Pension)
def pensions_post_delete(sender: object,
                         instance: object,
                         *args,
                         **kwargs):
    print(f'\n<< pensions post delete {args=}\n{kwargs=}\n')
    created = kwargs.get('created')
    SignalBase.pensions(sender, instance, created, 'delete')
