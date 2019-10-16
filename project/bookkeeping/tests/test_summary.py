import pandas as pd
import pytest
from mock import Mock
from pandas.api.types import is_numeric_dtype
from ...expenses.models import Expense
from ...incomes.models import Income
from ...savings.models import Saving
from ...transactions.models import SavingChange, SavingClose, Transaction
from ..lib.summary import collect_summary_data

pytestmark = pytest.mark.django_db

columns = [
    'i_past', 'i_now',
    'e_past', 'e_now',
    's_past', 's_now',
    'tr_from_past', 'tr_from_now',
    'tr_to_past', 'tr_to_now',
    's_close_to_past', 's_close_to_now',
    's_close_from_past', 's_close_from_now',
    's_change_to_past', 's_change_to_now',
    's_change_from_past', 's_change_from_now',
    's_change_from_fee_past', 's_change_from_fee_now',
]


def test_no_accounts_model_not_exists():
    (actual, _) = collect_summary_data(1999, ['X'])

    assert isinstance(actual, pd.DataFrame)
    assert actual.empty


def test_model_not_exists(incomes):
    (actual, _) = collect_summary_data(1999, ['X'])

    assert len(columns) == actual.shape[1]  # columns

    for col in columns:
        assert col in actual.columns


def test_model_dont_have_summary_method():
    model = Mock()
    model.objects.summary.side_effect = Exception('no summary')
    model.objects.summary_to.side_effect = Exception('no summary_to')
    model.objects.summary_from.side_effect = Exception('no summary_from')

    (actual, _) = collect_summary_data(1999, [model])

    assert isinstance(actual, pd.DataFrame)
    assert actual.empty


def test_model_summary_without_title():
    model = Mock()
    model.objects.summary.return_value = [{'x': 'x'}]
    model.objects.summary_to.side_effect = Exception('no summary_to')
    model.objects.summary_from.side_effect = Exception('no summary_from')

    (actual, _) = collect_summary_data(1999, [model])

    assert isinstance(actual, pd.DataFrame)
    assert actual.empty


def test_incomes_df_accounts(incomes):
    (actual, _) = collect_summary_data(1999, [Income])

    assert isinstance(actual, pd.DataFrame)

    assert 2 == actual.shape[0]  # rows

    assert 5.25 == actual.at['Account1', 'i_past']
    assert 3.25 == actual.at['Account1', 'i_now']

    assert 4.5 == actual.at['Account2', 'i_past']
    assert 3.5 == actual.at['Account2', 'i_now']


def test_df_dtypes(incomes):
    (actual, _) = collect_summary_data(1999, [Income])

    for col in columns:
        assert is_numeric_dtype(actual[col])


def test_df_have_nan(incomes):
    (actual, _) = collect_summary_data(1999, [Income])

    for col in columns:
        assert not actual[col].isnull().values.any()


def test_incomes_df_savings(incomes):
    (_, actual) = collect_summary_data(1999, [Income])

    assert isinstance(actual, pd.DataFrame)
    assert actual.empty


def test_incomes_qs_count(incomes, django_assert_max_num_queries):
    with django_assert_max_num_queries(4):
        [*collect_summary_data(1999, [Income])]


def test_expenses(expenses):
    (actual, _) = collect_summary_data(1999, [Expense])

    assert 2 == actual.shape[0]  # rows

    assert 2.5 == actual.at['Account1', 'e_past']
    assert 0.5 == actual.at['Account1', 'e_now']

    assert 2.25 == actual.at['Account2', 'e_past']
    assert 1.25 == actual.at['Account2', 'e_now']


def test_expenses_qs_count(expenses, django_assert_max_num_queries):
    with django_assert_max_num_queries(4):
        [*collect_summary_data(1999, [Expense])]


def test_savings(savings):
    (actual, _) = collect_summary_data(1999, [Saving])

    assert 2 == actual.shape[0]  # rows

    assert 1.25 == actual.at['Account1', 's_past']
    assert 3.5 == actual.at['Account1', 's_now']

    assert 0.25 == actual.at['Account2', 's_past']
    assert 2.25 == actual.at['Account2', 's_now']


def test_savings_qs_count(savings, django_assert_max_num_queries):
    with django_assert_max_num_queries(4):
        [*collect_summary_data(1999, [Saving])]


def test_transactions(transactions):
    (actual, _) = collect_summary_data(1999, [Transaction])

    assert 2 == actual.shape[0]  # rows

    assert 1.25 == actual.at['Account1', 'tr_from_past']
    assert 4.5 == actual.at['Account1', 'tr_from_now']
    assert 5.25 == actual.at['Account2', 'tr_from_past']
    assert 3.25 == actual.at['Account2', 'tr_from_now']

    assert 5.25 == actual.at['Account1', 'tr_to_past']
    assert 3.25 == actual.at['Account1', 'tr_to_now']
    assert 1.25 == actual.at['Account2', 'tr_to_past']
    assert 4.5 == actual.at['Account2', 'tr_to_now']


def test_transactions_qs_count(transactions, django_assert_max_num_queries):
    with django_assert_max_num_queries(6):
        [*collect_summary_data(1999, [Transaction])]


def test_saving_close_accounts(savings_close):
    (actual, _) = collect_summary_data(1999, [SavingClose])

    assert 2 == actual.shape[0]  # rows

    assert 0.25 == actual.at['Account1', 's_close_to_past']
    assert 0.25 == actual.at['Account1', 's_close_to_now']
    assert 0.0 == actual.at['Account2', 's_close_to_past']
    assert 0.0 == actual.at['Account2', 's_close_to_now']


def test_saving_close_saving_type(savings_close):
    (_, actual) = collect_summary_data(1999, [SavingClose])

    assert 1 == actual.shape[0]  # rows

    assert 0.25 == actual.at['Saving1', 's_close_from_past']
    assert 0.25 == actual.at['Saving1', 's_close_from_now']


def test_saving_close_qs_count(savings_close, django_assert_max_num_queries):
    with django_assert_max_num_queries(6):
        [*collect_summary_data(1999, [SavingClose])]


def test_saving_change_accounts(savings_change):
    (actual, _) = collect_summary_data(1999, [SavingChange])

    assert isinstance(actual, pd.DataFrame)
    assert actual.empty


def test_saving_change_saving_type(savings_change):
    (_, actual) = collect_summary_data(1999, [SavingChange])

    assert 2 == actual.shape[0]  # rows

    assert 's_change_from_past' in actual.columns
    assert 's_change_from_now' in actual.columns
    assert 's_change_from_fee_past' in actual.columns
    assert 's_change_from_fee_now' in actual.columns


def test_saving_change_qs_count(savings_change, django_assert_max_num_queries):
    with django_assert_max_num_queries(6):
        [*collect_summary_data(1999, [SavingChange])]


def test_all_qs_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(20):
        [*collect_summary_data(1999, [Income, Expense, Saving, SavingClose, SavingChange, Transaction])]
