from typing import Optional

from django.db import models

from ...accounts import models as account
from ...accounts.models import AccountBalance
from ...bookkeeping import models as bookkeeping
from ...debts.services.model_services import DebtModelService, DebtReturnModelService
from ...expenses.services.model_services import ExpenseModelService
from ...incomes.services.model_services import IncomeModelService
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
        lambda user: IncomeModelService(user).incomes(),
        lambda user: DebtModelService(user, "borrow").incomes(),
        lambda user: DebtReturnModelService(user, "lend").incomes(),
        lambda user: transaction.Transaction.objects.incomes(user),
        lambda user: transaction.SavingClose.objects.incomes(user),
    ),
    "expenses": (
        lambda user: ExpenseModelService(user).expenses(),
        lambda user: DebtModelService(user, "lend").expenses(),
        lambda user: DebtReturnModelService(user, "borrow").expenses(),
        lambda user: transaction.Transaction.objects.expenses(user),
        lambda user: saving.Saving.objects.expenses(user),
    ),
    "have": (lambda user: bookkeeping.AccountWorth.objects.have(user),),
    "types": (lambda user: account.Account.objects.related(user),),
}


SAVINGS_CONF = {
    "incomes": (
        lambda user: saving.Saving.objects.incomes(user),
        lambda user: transaction.SavingChange.objects.incomes(user),
    ),
    "expenses": (
        lambda user: transaction.SavingClose.objects.expenses(user),
        lambda user: transaction.SavingChange.objects.expenses(user),
    ),
    "have": (lambda user: bookkeeping.SavingWorth.objects.have(user),),
    "types": (lambda user: saving.SavingType.objects.related(user),),
}


PENSIONS_CONF = {
    "incomes": (lambda user: pension.Pension.objects.incomes(user),),
    "have": (lambda user: bookkeeping.PensionWorth.objects.have(user),),
    "types": (lambda user: pension.PensionType.objects.related(user),),
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
