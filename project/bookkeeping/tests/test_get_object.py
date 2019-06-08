import pandas as pd
import pytest

from ..lib.get_data import GetObject as T
from ...incomes.models import Income

pytestmark = pytest.mark.django_db


def test_incomes_type():
    actual = T(Income).df

    assert isinstance(actual, pd.DataFrame)


def test_incomes_len(_incomes):
    actual = T(Income).df

    assert 4 == len(actual)


def test_incomes_amount_values(_incomes):
    actual = T(Income).df

    assert 1000 == actual.loc[actual.date == '1999-01-01', 'amount'].values
    assert 2000 == actual.loc[actual.date == '1999-01-31', 'amount'].values
    assert 5000 == actual.loc[actual.date == '1970-01-01', 'amount'].values
    assert 2000 == actual.loc[actual.date == '1970-11-01', 'amount'].values
