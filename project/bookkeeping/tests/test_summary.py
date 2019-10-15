import pandas as pd
import pytest
from mock import Mock

from ...expenses.models import Expense
from ...incomes.models import Income
from ...savings.models import Saving
from ..lib.summary import collect_summary_data
from ...transactions.models import Transaction, SavingClose

pytestmark = pytest.mark.django_db


def test_model_not_exists(incomes):
    (actual, _) = collect_summary_data(1999, ['X'])

    assert isinstance(actual, pd.DataFrame)
    assert actual.empty


def test_model_dont_have_summary_method(incomes):
    model = Mock()
    model.objects.summary.side_effect = Exception('no summary')
    model.objects.summary_to.side_effect = Exception('no summary_to')
    model.objects.summary_from.side_effect = Exception('no summary_from')

    (actual, _) = collect_summary_data(1999, [model])

    assert isinstance(actual, pd.DataFrame)
    assert actual.empty


def test_incomes_df_accounts(incomes):
    (actual, _) = collect_summary_data(1999, [Income])

    assert isinstance(actual, pd.DataFrame)

    assert 2 == actual.shape[0]  # rows
    assert 2 == actual.shape[1]  # columns

    assert 'i_past' in actual.columns
    assert 'i_now' in actual.columns

    assert 'Account1' == actual.index.values[0]
    assert 'Account2' == actual.index.values[1]

    assert 5.25 == actual.at['Account1', 'i_past']
    assert 3.25 == actual.at['Account1', 'i_now']

    assert 4.5 == actual.at['Account2', 'i_past']
    assert 3.5 == actual.at['Account2', 'i_now']


def test_incomes_df_savings(incomes):
    (_, actual) = collect_summary_data(1999, [Income])

    assert isinstance(actual, pd.DataFrame)
    assert actual.empty


def test_incomes_qs_count(incomes, django_assert_max_num_queries):
    with django_assert_max_num_queries(3):
        [*collect_summary_data(1999, [Income])]


def test_expenses(expenses):
    (actual, _) = collect_summary_data(1999, [Expense])

    assert isinstance(actual, pd.DataFrame)

    assert 2 == actual.shape[0]  # rows
    assert 2 == actual.shape[1]  # columns

    assert 'e_past' in actual.columns
    assert 'e_now' in actual.columns

    assert 'Account1' == actual.index.values[0]
    assert 'Account2' == actual.index.values[1]

    assert 2.5 == actual.at['Account1', 'e_past']
    assert 0.5 == actual.at['Account1', 'e_now']

    assert 2.25 == actual.at['Account2', 'e_past']
    assert 1.25 == actual.at['Account2', 'e_now']


def test_expenses_qs_count(expenses, django_assert_max_num_queries):
    with django_assert_max_num_queries(3):
        [*collect_summary_data(1999, [Expense])]


def test_savings(savings):
    (actual, _) = collect_summary_data(1999, [Saving])

    assert isinstance(actual, pd.DataFrame)

    assert 2 == actual.shape[0]  # rows
    assert 2 == actual.shape[1]  # columns

    assert 's_past' in actual.columns
    assert 's_now' in actual.columns

    assert 'Account1' == actual.index.values[0]
    assert 'Account2' == actual.index.values[1]

    assert 1.25 == actual.at['Account1', 's_past']
    assert 3.5 == actual.at['Account1', 's_now']

    assert 0.25 == actual.at['Account2', 's_past']
    assert 2.25 == actual.at['Account2', 's_now']


def test_savings_qs_count(savings, django_assert_max_num_queries):
    with django_assert_max_num_queries(3):
        [*collect_summary_data(1999, [Saving])]


def test_transactions(transactions):
    (actual, _) = collect_summary_data(1999, [Transaction])

    assert isinstance(actual, pd.DataFrame)

    assert 2 == actual.shape[0]  # rows
    assert 4 == actual.shape[1]  # columns

    assert 'tr_from_past' in actual.columns
    assert 'tr_from_now' in actual.columns
    assert 'tr_to_past' in actual.columns
    assert 'tr_to_now' in actual.columns

    assert 1.25 == actual.at['Account1', 'tr_from_past']
    assert 4.5 == actual.at['Account1', 'tr_from_now']
    assert 5.25 == actual.at['Account2', 'tr_from_past']
    assert 3.25 == actual.at['Account2', 'tr_from_now']

    assert 5.25 == actual.at['Account1', 'tr_to_past']
    assert 3.25 == actual.at['Account1', 'tr_to_now']
    assert 1.25 == actual.at['Account2', 'tr_to_past']
    assert 4.5 == actual.at['Account2', 'tr_to_now']


def test_transactions_qs_count(transactions, django_assert_max_num_queries):
    with django_assert_max_num_queries(4):
        [*collect_summary_data(1999, [Transaction])]


def test_saving_close_accounts(savings_close):
    (actual, _) = collect_summary_data(1999, [SavingClose])

    assert isinstance(actual, pd.DataFrame)

    assert 2 == actual.shape[0]  # rows
    assert 2 == actual.shape[1]  # columns

    assert 's_close_to_past' in actual.columns
    assert 's_close_to_now' in actual.columns

    assert 0.25 == actual.at['Account1', 's_close_to_past']
    assert 0.25 == actual.at['Account1', 's_close_to_now']
    assert 0.0 == actual.at['Account2', 's_close_to_past']
    assert 0.0 == actual.at['Account2', 's_close_to_now']


def test_saving_close_saving_type(savings_close):
    (_, actual) = collect_summary_data(1999, [SavingClose])

    assert isinstance(actual, pd.DataFrame)

    assert 1 == actual.shape[0]  # rows
    assert 2 == actual.shape[1]  # columns

    assert 's_close_from_past' in actual.columns
    assert 's_close_from_now' in actual.columns

    assert 0.25 == actual.at['Saving1', 's_close_from_past']
    assert 0.25 == actual.at['Saving1', 's_close_from_now']


def test_saving_close_qs_count(savings_close, django_assert_max_num_queries):
    with django_assert_max_num_queries(4):
        [*collect_summary_data(1999, [SavingClose])]
