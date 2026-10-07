from ..accounts.services.model_services import (
    AccountBalanceModelService,
    AccountModelService,
)
from ..core.lib.signals import Accounts, Savings
from ..core.services.signals_service import sync
from ..debts.models import Debt
from ..debts.services.model_services import DebtModelService, DebtReturnModelService
from ..expenses.services.model_services import ExpenseModelService
from ..incomes.services.model_services import IncomeModelService
from ..pensions.services.model_services import (
    PensionBalanceModelService,
    PensionModelService,
    PensionTypeModelService,
)
from ..savings.services.model_services import (
    SavingBalanceModelService,
    SavingModelService,
    SavingTypeModelService,
)
from ..transactions.services.model_services import (
    SavingChangeModelService,
    SavingCloseModelService,
    TransactionModelService,
)
from ..users.models import User
from .services.model_services import (
    AccountWorthModelService,
    PensionWorthModelService,
    SavingWorthModelService,
)

ACCOUNTS = {
    "incomes": (
        lambda user: IncomeModelService(user).incomes(),
        lambda user: DebtModelService(user, Debt.DebtType.BORROW).incomes(),
        lambda user: DebtReturnModelService(user, Debt.DebtType.LEND).incomes(),
        lambda user: TransactionModelService(user).incomes(),
        lambda user: SavingCloseModelService(user).incomes(),
    ),
    "expenses": (
        lambda user: ExpenseModelService(user).expenses(),
        lambda user: DebtModelService(user, Debt.DebtType.LEND).expenses(),
        lambda user: DebtReturnModelService(user, Debt.DebtType.BORROW).expenses(),
        lambda user: TransactionModelService(user).expenses(),
        lambda user: SavingModelService(user).expenses(),
    ),
    "have": (lambda user: AccountWorthModelService(user).have(),),
    "types": (lambda user: AccountModelService(user).all(),),
}


SAVINGS = {
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


PENSIONS = {
    "incomes": (lambda user: PensionModelService(user).incomes(),),
    "have": (lambda user: PensionWorthModelService(user).have(),),
    "types": (lambda user: PensionTypeModelService(user).items(),),
}


def sync_accounts(user: User) -> None:
    sync(user, ACCOUNTS, Accounts, AccountBalanceModelService)


def sync_savings(user: User) -> None:
    sync(user, SAVINGS, Savings, SavingBalanceModelService)


def sync_pensions(user: User) -> None:
    sync(user, PENSIONS, Savings, PensionBalanceModelService)
