from datetime import date

import pandas as pd
import pytest
from mock import Mock
from pandas.api.types import is_numeric_dtype

from ...expenses.models import Expense
from ...incomes.models import Income
from ...savings.factories import SavingFactory, SavingTypeFactory
from ...savings.models import Saving
from ...transactions.models import SavingChange, SavingClose, Transaction
from ..lib.summary import collect_summary_data

pytestmark = pytest.mark.django_db

columns = [
    'i_past', 'i_now',
    'e_past', 'e_now',
    's_past', 's_now',
    's_fee_past', 's_fee_now',
    'tr_from_past', 'tr_from_now',
    'tr_to_past', 'tr_to_now',
    's_close_to_past', 's_close_to_now',
    's_close_from_past', 's_close_from_now',
    's_change_to_past', 's_change_to_now',
    's_change_from_past', 's_change_from_now',
    's_change_from_fee_past', 's_change_from_fee_now',
    's_change_to_fee_past', 's_change_to_fee_now',
]


@pytest.fixture()
def account_types():
    return ['Account1', 'Account2']


@pytest.fixture()
def saving_types():
    return ['Saving1', 'Saving2']


def test_no_accounts_model_not_exists():
    actual = collect_summary_data(1999, [], ['X'])

    assert isinstance(actual, pd.DataFrame)
    assert actual.empty


def test_model_not_exists(account_types, incomes):
    actual = collect_summary_data(1999, account_types, ['X'])

    assert len(columns) == actual.shape[1]  # columns

    for col in columns:
        assert col in actual.columns


def test_model_dont_have_summary_method():
    model = Mock()
    model.objects.summary.side_effect = Exception('no summary')
    model.objects.summary_to.side_effect = Exception('no summary_to')
    model.objects.summary_from.side_effect = Exception('no summary_from')

    actual = collect_summary_data(1999, [], [model])

    assert isinstance(actual, pd.DataFrame)
    assert actual.empty


def test_model_summary_without_title():
    model = Mock()
    model.objects.summary.return_value = [{'x': 'x'}]
    model.objects.summary_to.side_effect = Exception('no summary_to')
    model.objects.summary_from.side_effect = Exception('no summary_from')

    actual = collect_summary_data(1999, [], [model])

    assert isinstance(actual, pd.DataFrame)
    assert actual.empty


def test_incomes_df_accounts(account_types, incomes):
    actual = collect_summary_data(1999, account_types, [Income])

    assert isinstance(actual, pd.DataFrame)

    assert 2 == actual.shape[0]  # rows

    assert 5.25 == actual.at['Account1', 'i_past']
    assert 3.25 == actual.at['Account1', 'i_now']

    assert 4.5 == actual.at['Account2', 'i_past']
    assert 3.5 == actual.at['Account2', 'i_now']


def test_df_dtypes(account_types, incomes):
    actual = collect_summary_data(1999, account_types, [Income])

    for col in columns:
        assert is_numeric_dtype(actual[col])


def test_df_have_nan(account_types, incomes):
    actual = collect_summary_data(1999, account_types, [Income])

    for col in columns:
        assert not actual[col].isnull().values.any()


def test_incomes_df_savings(incomes):
    actual = collect_summary_data(1999, [], [Income])

    assert isinstance(actual, pd.DataFrame)
    assert actual.empty


def test_incomes_qs_count(account_types, incomes, django_assert_max_num_queries):
    with django_assert_max_num_queries(2):
        [*collect_summary_data(1999, account_types, [Income])]


def test_expenses(account_types, expenses):
    actual = collect_summary_data(1999, account_types, [Expense])

    assert 2 == actual.shape[0]  # rows

    assert 2.5 == actual.at['Account1', 'e_past']
    assert 0.5 == actual.at['Account1', 'e_now']

    assert 2.25 == actual.at['Account2', 'e_past']
    assert 1.25 == actual.at['Account2', 'e_now']


def test_expenses_qs_count(account_types, expenses, django_assert_max_num_queries):
    with django_assert_max_num_queries(2):
        [*collect_summary_data(1999, account_types, [Expense])]


def test_savings_for_accounts(account_types, savings):
    actual = collect_summary_data(1999, account_types, [Saving])

    assert 2 == actual.shape[0]  # rows

    assert 1.25 == actual.at['Account1', 's_past']
    assert 3.5 == actual.at['Account1', 's_now']

    assert 0.25 == actual.at['Account2', 's_past']
    assert 2.25 == actual.at['Account2', 's_now']


def test_savings_for_savings_with_fees(saving_types, savings):
    actual = collect_summary_data(1999, saving_types, [Saving])

    assert 2 == actual.shape[0]  # rows

    assert 0.25 == actual.at['Saving1', 's_fee_past']
    assert 0.5 == actual.at['Saving1', 's_fee_now']

    assert 0.0 == actual.at['Saving2', 's_fee_past']
    assert 0.25 == actual.at['Saving2', 's_fee_now']


def test_saving_for_savings_with_closed():
    s1 = SavingTypeFactory(title='S1')
    s2 = SavingTypeFactory(title='S2', closed=1974)

    SavingFactory(date=date(1999, 1, 1), saving_type=s1)
    SavingFactory(date=date(1999, 1, 1), saving_type=s2)

    actual = collect_summary_data(1999, ['S1'], [Saving])

    assert 1 == actual.shape[0]  # rows


def test_savings_qs_count(account_types, savings, django_assert_max_num_queries):
    with django_assert_max_num_queries(2):
        [*collect_summary_data(1999, account_types, [Saving])]


def test_transactions(account_types, transactions):
    actual = collect_summary_data(1999, account_types, [Transaction])

    assert 2 == actual.shape[0]  # rows

    assert 1.25 == actual.at['Account1', 'tr_from_past']
    assert 4.5 == actual.at['Account1', 'tr_from_now']
    assert 5.25 == actual.at['Account2', 'tr_from_past']
    assert 3.25 == actual.at['Account2', 'tr_from_now']

    assert 5.25 == actual.at['Account1', 'tr_to_past']
    assert 3.25 == actual.at['Account1', 'tr_to_now']
    assert 1.25 == actual.at['Account2', 'tr_to_past']
    assert 4.5 == actual.at['Account2', 'tr_to_now']


def test_transactions_qs_count(account_types, transactions, django_assert_max_num_queries):
    with django_assert_max_num_queries(4):
        [*collect_summary_data(1999, account_types, [Transaction])]


def test_saving_close_accounts(account_types, savings_close):
    actual = collect_summary_data(1999, account_types, [SavingClose])

    assert 2 == actual.shape[0]  # rows

    assert 0.25 == actual.at['Account1', 's_close_to_past']
    assert 0.25 == actual.at['Account1', 's_close_to_now']
    assert 0.0 == actual.at['Account2', 's_close_to_past']
    assert 0.0 == actual.at['Account2', 's_close_to_now']


def test_saving_close_saving_type(savings_close):
    actual = collect_summary_data(1999, ['Saving1'], [SavingClose])

    assert 1 == actual.shape[0]  # rows

    assert 0.25 == actual.at['Saving1', 's_close_from_past']
    assert 0.25 == actual.at['Saving1', 's_close_from_now']


def test_saving_close_qs_count(saving_types, savings_close, django_assert_max_num_queries):
    with django_assert_max_num_queries(4):
        [*collect_summary_data(1999, saving_types, [SavingClose])]


def test_saving_change_accounts(savings_change):
    actual = collect_summary_data(1999, [], [SavingChange])

    assert isinstance(actual, pd.DataFrame)
    assert actual.empty


def test_saving_change_saving_type(saving_types, savings_change):
    actual = collect_summary_data(1999, saving_types, [SavingChange])

    assert 2 == actual.shape[0]  # rows


def test_saving_change_qs_count(saving_types, savings_change, django_assert_max_num_queries):
    with django_assert_max_num_queries(4):
        [*collect_summary_data(1999, saving_types, [SavingChange])]


def test_all_qs_count_for_accounts(account_types, django_assert_max_num_queries):
    with django_assert_max_num_queries(8):
        models = [Income, Expense, Saving, SavingClose, Transaction]
        [*collect_summary_data(1999, account_types, models)]


def test_all_qs_count_for_savings(saving_types, django_assert_max_num_queries):
    with django_assert_max_num_queries(6):
        models = [Saving, SavingClose, SavingChange]
        [*collect_summary_data(1999, saving_types, models)]
