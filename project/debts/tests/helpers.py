from django.db import connection
from django.test.utils import CaptureQueriesContext

from ..models import Debt
from .factories import (
    BorrowFactory,
    BorrowReturnFactory,
    LendFactory,
    LendReturnFactory,
)

DEBT_TYPES = [Debt.DebtType.LEND, Debt.DebtType.BORROW]

DEBT_FACTORIES = {Debt.DebtType.LEND: LendFactory, Debt.DebtType.BORROW: BorrowFactory}
RETURN_FACTORIES = {
    Debt.DebtType.LEND: LendReturnFactory,
    Debt.DebtType.BORROW: BorrowReturnFactory,
}


def assert_balance(actual, *, incomes, expenses, balance, title="Account1"):
    assert actual.account.title == title
    assert actual.incomes == incomes
    assert actual.expenses == expenses
    assert actual.balance == balance


def account_read_queries(service):
    with CaptureQueriesContext(connection) as captured:
        for row in service.objects:
            row.account.title
    return len(captured)
