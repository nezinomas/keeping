from typing import Optional

from django.db import models

from ...accounts import models as account
from ...accounts.models import AccountBalance
from ...bookkeeping import models as bookkeeping
from ...debts import models as debt
from ...expenses import models as expense
from ...incomes import models as income
from ...pensions import models as pension
from ...pensions.models import PensionBalance
from ...savings import models as saving
from ...savings.models import SavingBalance
from ...transactions import models as transaction
from ...users.models import User
from ..lib.db_sync import BalanceSynchronizer
from ..lib.signals import Accounts, GetData, Savings

ACCOUNTS_CONF = {
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


SAVINGS_CONF = {
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


PENSIONS_CONF = {
    "incomes": (pension.Pension,),
    "have": (bookkeeping.PensionWorth,),
    "types": (pension.PensionType,),
}


def sync_accounts(instance: models.Model, user: Optional[User] = None):
    user = user or _get_user_from_instance(instance)
    if not user:
        return

    get_data = GetData(user, ACCOUNTS_CONF)
    data = Accounts(get_data)

    BalanceSynchronizer(AccountBalance, user, data.df)


def sync_savings(instance: models.Model, user: Optional[User] = None):
    user = user or _get_user_from_instance(instance)
    if not user:
        return

    get_data = GetData(user, SAVINGS_CONF)
    data = Savings(get_data)

    BalanceSynchronizer(SavingBalance, user, data.df)


def sync_pensions(instance: models.Model, user: Optional[User] = None):
    user = user or _get_user_from_instance(instance)

    if not user:
        return

    get_data = GetData(user, PENSIONS_CONF)
    data = Savings(get_data)

    BalanceSynchronizer(PensionBalance, user, data.df)


def _get_user_from_instance(instance: models.Model) -> Optional[User]:
    """Return the user via the first FK field."""
    try:
        # Get first FK field name
        fk_field = next(
            f.name
            for f in instance._meta.get_fields()
            if f.many_to_one and not f.auto_created
        )
        # Follow FK → related object → journal -> first user
        related = getattr(instance, fk_field)
        journal = getattr(related, "journal", None)
        return journal.users.first()
    except StopIteration:
        return None
