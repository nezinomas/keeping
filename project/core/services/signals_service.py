from typing import Optional

from django.db import models

from ...accounts.models import AccountBalance
from ...accounts.services.model_services import AccountModelService
from ...bookkeeping.services.model_services import (
    AccountWorthModelService,
    PensionWorthModelService,
    SavingWorthModelService,
)
from ...debts.services.model_services import DebtModelService, DebtReturnModelService
from ...expenses.services.model_services import ExpenseModelService
from ...incomes.services.model_services import IncomeModelService
from ...pensions.models import PensionBalance
from ...pensions.services.model_services import (
    PensionModelService,
    PensionTypeModelService,
)
from ...savings.models import SavingBalance
from ...savings.services.model_services import (
    SavingModelService,
    SavingTypeModelService,
)
from ...transactions.services.model_services import (
    SavingChangeModelService,
    SavingCloseModelService,
    TransactionModelService,
)
from ...users.models import User
from ..lib.db_sync import BalanceSynchronizer
from ..lib.signals import Accounts, GetData, Savings

ACCOUNTS_CONF = {
    "incomes": (
        lambda user: IncomeModelService(user).incomes(),
        lambda user: DebtModelService(user, "borrow").incomes(),
        lambda user: DebtReturnModelService(user, "lend").incomes(),
        lambda user: TransactionModelService(user).incomes(),
        lambda user: SavingCloseModelService(user).incomes(),
    ),
    "expenses": (
        lambda user: ExpenseModelService(user).expenses(),
        lambda user: DebtModelService(user, "lend").expenses(),
        lambda user: DebtReturnModelService(user, "borrow").expenses(),
        lambda user: TransactionModelService(user).expenses(),
        lambda user: SavingModelService(user).expenses(),
    ),
    "have": (lambda user: AccountWorthModelService(user).have(),),
    "types": (lambda user: AccountModelService(user).all(),),
}


SAVINGS_CONF = {
    "incomes": (
        lambda user: SavingModelService(user).incomes(),
        lambda user: SavingChangeModelService(user).incomes(),
    ),
    "expenses": (
        lambda user: SavingCloseModelService(user).expenses(),
        lambda user: SavingChangeModelService(user).expenses(),
    ),
    "have": (lambda user: SavingWorthModelService(user).have(),),
    "types": (lambda user: SavingTypeModelService(user).all(),),
}


PENSIONS_CONF = {
    "incomes": (lambda user: PensionModelService(user).incomes(),),
    "have": (lambda user: PensionWorthModelService(user).have(),),
    "types": (lambda user: PensionTypeModelService(user).items(),),
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
