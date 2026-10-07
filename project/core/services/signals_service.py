from django.db import models

from ...accounts.services.model_services import (
    AccountBalanceModelService,
    AccountModelService,
)
from ...bookkeeping.services.model_services import (
    AccountWorthModelService,
    PensionWorthModelService,
    SavingWorthModelService,
)
from ...debts.services.model_services import DebtModelService, DebtReturnModelService
from ...expenses.services.model_services import ExpenseModelService
from ...incomes.services.model_services import IncomeModelService
from ...pensions.services.model_services import (
    PensionBalanceModelService,
    PensionModelService,
    PensionTypeModelService,
)
from ...savings.services.model_services import (
    SavingBalanceModelService,
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
    "moves": (
        lambda user: SavingCloseModelService(user).moves(),
        lambda user: SavingChangeModelService(user).moves(),
    ),
    "have": (lambda user: SavingWorthModelService(user).have(),),
    "types": (lambda user: SavingTypeModelService(user).all(),),
}


PENSIONS_CONF = {
    "incomes": (lambda user: PensionModelService(user).incomes(),),
    "have": (lambda user: PensionWorthModelService(user).have(),),
    "types": (lambda user: PensionTypeModelService(user).items(),),
}


def sync_accounts(user: User):
    _sync_data(user, ACCOUNTS_CONF, Accounts, AccountBalanceModelService)


def sync_savings(user: User):
    _sync_data(user, SAVINGS_CONF, Savings, SavingBalanceModelService)


def sync_pensions(user: User):
    _sync_data(user, PENSIONS_CONF, Savings, PensionBalanceModelService)


def _sync_data(user: User, conf: dict, signal_cls, sync_model_service):
    data = signal_cls(GetData(user, conf))
    BalanceSynchronizer(sync_model_service, user, data.df)


def journal_user(instance: models.Model) -> User:
    return instance.journal.users.earliest("pk")
