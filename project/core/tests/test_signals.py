from datetime import datetime, timezone

from ...accounts.factories import AccountFactory
from ...accounts.models import AccountBalance
from ..signals import create_objects


def test_create_objects():
    account = AccountFactory.build()

    data = [
        dict(
            id=1, year=1999, past=1.0, incomes=2.0, expenses=3.0, balance=4.0, have=5.0, delta=6.0, latest_check=datetime(1999, 1, 1, 3, 2, 1, tzinfo=timezone.utc))
    ]
    actual = create_objects(AccountBalance, {1: account}, data)[0]

    assert actual.account == account
    assert actual.year == 1999
    assert actual.past == 1.0
    assert actual.incomes == 2.0
    assert actual.expenses == 3.0
    assert actual.balance == 4.0
    assert actual.have == 5.0
    assert actual.delta == 6.0
    assert actual.latest_check == datetime(1999, 1, 1, 3, 2, 1, tzinfo=timezone.utc)
