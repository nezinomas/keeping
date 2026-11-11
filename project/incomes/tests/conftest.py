from datetime import date

import factory
import pytest
from django.db.models.signals import post_save

from ...accounts.tests.factories import AccountFactory
from .factories import IncomeFactory


@pytest.fixture()
def incomes():
    """project/conftest.py's rows with no balance sync: incomes' sums read rows only."""
    a1 = AccountFactory(title="Account1")
    a2 = AccountFactory(title="Account2")

    with factory.django.mute_signals(post_save):
        IncomeFactory(price=525, date=date(1970, 1, 1), account=a1)
        IncomeFactory(price=225, date=date(1970, 1, 1), account=a2)
        IncomeFactory(price=225, date=date(1970, 1, 31), account=a2)
        IncomeFactory(price=325, date=date(1999, 1, 1), account=a1)
        IncomeFactory(price=225, date=date(1999, 1, 1), account=a2)
        IncomeFactory(price=125, date=date(1999, 2, 1), account=a2)
