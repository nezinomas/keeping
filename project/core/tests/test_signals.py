from datetime import datetime, timezone

from ...accounts.factories import AccountFactory
from ...accounts.models import AccountBalance
from ..signals import create_objects


def test_create_objects():
    account = AccountFactory.build()

    data = [
        dict(
            id=1,
            year=1999,
            past=1,
            incomes=2,
            expenses=3,
            balance=4,
            have=5,
            delta=6,
            latest_check=datetime(1999, 1, 1, 3, 2, 1),
        )
    ]
    actual = create_objects(AccountBalance, {1: account}, data)[0]

    assert actual.account == account
    assert actual.year == 1999
    assert actual.past == 1
    assert actual.incomes == 2
    assert actual.expenses == 3
    assert actual.balance == 4
    assert actual.have == 5
    assert actual.delta == 6
    assert actual.latest_check == datetime(1999, 1, 1, 3, 2, 1, tzinfo=timezone.utc)
