import pandas as pd
import pytest

from ..lib.get_data import GetObject as T
from ...incomes.models import Income
from ...accounts.models import Account

pytestmark = pytest.mark.django_db


def test_incomes_type():
    actual = T(Income).df

    assert isinstance(actual, pd.DataFrame)


def test_incomes_len(_incomes_from_db):
    actual = T(Income).df

    assert 2 == len(actual)


def test_incomes_price_values(_incomes_from_db):
    actual = T(Income).df

    assert 5000 == actual.loc[actual.date == '1970-01-01', 'price'].values
    assert 2000 == actual.loc[actual.date == '1999-01-31', 'price'].values


def test_incomes_account_titles(_incomes_from_db):
    actual = T(Income).df

    assert 'Account1' == actual.loc[actual.date == '1970-01-01', 'account'].values
    assert 'Account2' == actual.loc[actual.date == '1999-01-31', 'account'].values


def test_account_list_for_value_list():
    actual, _ = T(Account)._get_fields()

    expect = ['id', 'title', 'slug', 'order']

    assert expect == actual


def test_account_list_for_dataframe_colums():
    _, actual = T(Account)._get_fields()

    expect = ['id', 'title', 'slug', 'order']

    assert expect == actual


def test_income_list_for_value_list():
    actual, _ = T(Income)._get_fields()

    expect = ['id', 'date', 'price', 'remark',
              'account__title', 'income_type__title']

    assert expect == actual


def test_income_list_for_dataframe_colums():
    _, actual = T(Income)._get_fields()

    expect = ['id', 'date', 'price', 'remark', 'account', 'income_type']

    assert expect == actual
