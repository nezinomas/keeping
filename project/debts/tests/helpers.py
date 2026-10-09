from .factories import (
    BorrowFactory,
    BorrowReturnFactory,
    LendFactory,
    LendReturnFactory,
)

DEBT_TYPES = ["lend", "borrow"]

DEBT_FACTORIES = {"lend": LendFactory, "borrow": BorrowFactory}
RETURN_FACTORIES = {"lend": LendReturnFactory, "borrow": BorrowReturnFactory}


def assert_balance(actual, *, incomes, expenses, balance, title="Account1"):
    assert actual.account.title == title
    assert actual.incomes == incomes
    assert actual.expenses == expenses
    assert actual.balance == balance
