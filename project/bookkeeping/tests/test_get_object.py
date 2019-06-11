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

    assert 5 == len(actual)


def test_incomes_price_values(_incomes):
    actual = T(Income).df

    assert 5000 == actual.loc[actual.date == '1970-01-01', 'price'].values
    assert 2000 == actual.loc[actual.date == '1970-11-01', 'price'].values
    assert 3000 == actual.loc[actual.date == '1999-01-01', 'price'].values
    assert 2000 == actual.loc[actual.date == '1999-01-02', 'price'].values
    assert 2000 == actual.loc[actual.date == '1999-01-31', 'price'].values


def test_incomes_account_titles(_incomes):
    actual = T(Income).df

    assert 'Account1' == actual.loc[actual.date == '1970-01-01', 'account'].values
    assert 'Account2' == actual.loc[actual.date == '1970-11-01', 'account'].values
    assert 'Account1' == actual.loc[actual.date == '1999-01-01', 'account'].values
    assert 'Account2' == actual.loc[actual.date == '1999-01-02', 'account'].values
    assert 'Account2' == actual.loc[actual.date == '1999-01-31', 'account'].values
