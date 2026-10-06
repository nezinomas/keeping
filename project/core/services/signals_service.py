from django.db import models

from ...accounts.services.model_services import (
    AccountBalanceModelService,
    AccountModelService,
)
from ...bookkeeping.models import AccountWorth, PensionWorth, SavingWorth
from ...bookkeeping.services.model_services import (
    AccountWorthModelService,
    PensionWorthModelService,
    SavingWorthModelService,
)
from ...debts.models import DebtReturn
from ...debts.services.model_services import DebtModelService, DebtReturnModelService
from ...expenses.models import Expense
from ...expenses.services.model_services import ExpenseModelService
from ...incomes.models import Income
from ...incomes.services.model_services import IncomeModelService
from ...journals.models import Journal
from ...pensions.models import Pension
from ...pensions.services.model_services import (
    PensionBalanceModelService,
    PensionModelService,
    PensionTypeModelService,
)
from ...savings.models import Saving
from ...savings.services.model_services import (
    SavingBalanceModelService,
    SavingModelService,
    SavingTypeModelService,
)
from ...transactions.models import SavingChange, SavingClose, Transaction
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


JOURNAL_FK = {
    Income: "account",
    Expense: "expense_type",
    Saving: "saving_type",
    Transaction: "from_account",
    SavingClose: "from_account",
    SavingChange: "from_account",
    DebtReturn: "account",
    AccountWorth: "account",
    SavingWorth: "saving_type",
    PensionWorth: "pension_type",
    Pension: "pension_type",
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
    """The first user of the instance's journal."""
    return _journal_of(instance).users.earliest("pk")


def _journal_of(instance: models.Model) -> Journal:
    """The instance's own journal, else the journal of the FK it hangs from."""
    if hasattr(instance, "journal_id"):
        return instance.journal

    return getattr(instance, JOURNAL_FK[type(instance)]).journal
