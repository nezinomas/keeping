from datetime import date

import pandas as pd
import pytest
from django.apps import apps
from mock import Mock, patch
from pandas.api.types import is_numeric_dtype

from ...savings.factories import SavingFactory, SavingTypeFactory
from ..lib.summary import collect_summary_data

pytestmark = pytest.mark.django_db

columns = [
    'id',
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
]


@pytest.fixture()
def account_types():
    return {'Account1': 1, 'Account2': 2}


@pytest.fixture()
def saving_types():
    return {'Saving1': 1, 'Saving2': 2}


@patch('project.core.lib.summary.models',
       return_value={'incomes.Income'})
def test_no_accounts_model_not_exists(mock_models):
    actual = collect_summary_data(1999, [], 'accounts')

    assert isinstance(actual, pd.DataFrame)
    assert actual.empty


@patch('project.core.lib.summary.models',
       return_value={'incomes.Income'})
def test_model_not_exists(mock_models, account_types):
    actual = collect_summary_data(1999, account_types, 'accounts')

    assert len(columns) == actual.shape[1]  # columns

    for col in columns:
        assert col in actual.columns


@patch('project.core.lib.summary.models',
       return_value={'incomes.Income'})
@patch('django.apps.apps.get_model')
def test_model_dont_have_summary_method(mock_get, mock_models):
    model = Mock()
    model.objects.summary.side_effect = Exception('no summary')
    model.objects.summary_to.side_effect = Exception('no summary_to')
    model.objects.summary_from.side_effect = Exception('no summary_from')

    mock_get.return_value = model

    actual = collect_summary_data(1999, {}, 'accounts')

    assert isinstance(actual, pd.DataFrame)
    assert actual.empty


@patch('project.core.lib.summary.models',
       return_value={'incomes.Income'})
@patch('django.apps.apps.get_model')
def test_model_summary_without_title(mock_get, mock_models):
    model = Mock()
    model.objects.summary.return_value = [{'x': 'x'}]
    model.objects.summary_to.side_effect = Exception('no summary_to')
    model.objects.summary_from.side_effect = Exception('no summary_from')

    mock_get.return_value = model
    actual = collect_summary_data(1999, {}, 'accounts')

    assert isinstance(actual, pd.DataFrame)
    assert actual.empty


@patch('project.core.lib.summary.models',
       return_value={'incomes.Income'})
def test_incomes_df_accounts(mock_models, account_types, incomes):
    actual = collect_summary_data(1999, account_types, 'accounts')

    assert isinstance(actual, pd.DataFrame)

    assert 2 == actual.shape[0]  # rows

    assert 1 == actual.at['Account1', 'id']
    assert 5.25 == actual.at['Account1', 'i_past']
    assert 3.25 == actual.at['Account1', 'i_now']

    assert 2 == actual.at['Account2', 'id']
    assert 4.5 == actual.at['Account2', 'i_past']
    assert 3.5 == actual.at['Account2', 'i_now']


@patch('project.core.lib.summary.models',
       return_value={'incomes.Income'})
def test_incomes_df_accounts_only_one_account(mock_models, incomes):
    actual = collect_summary_data(1999, {'Account1': 1}, 'accounts')

    assert isinstance(actual, pd.DataFrame)

    assert 1 == actual.shape[0]  # rows

    assert 1 == actual.at['Account1', 'id']
    assert 5.25 == actual.at['Account1', 'i_past']
    assert 3.25 == actual.at['Account1', 'i_now']


@patch('project.core.lib.summary.models',
       return_value={'incomes.Income'})
def test_df_dtypes(mock_models, account_types, incomes):
    actual = collect_summary_data(1999, account_types, 'accounts')

    for col in columns:
        assert is_numeric_dtype(actual[col])


@patch('project.core.lib.summary.models',
       return_value={'incomes.Income'})
def test_df_have_nan(mock_models, account_types, incomes):
    actual = collect_summary_data(1999, account_types, 'accounts')

    for col in columns:
        assert not actual[col].isnull().values.any()


@patch('project.core.lib.summary.models',
       return_value={'incomes.Income'})
def test_incomes_df_savings(mock_models, incomes):
    actual = collect_summary_data(1999, {}, 'accounts')

    assert isinstance(actual, pd.DataFrame)
    assert actual.empty


@patch('project.core.lib.summary.models',
       return_value={'incomes.Income'})
def test_incomes_qs_count(mock_models,
                          account_types, incomes,
                          django_assert_max_num_queries):
    with django_assert_max_num_queries(2):
        [*collect_summary_data(1999, account_types, 'accounts')]


@patch('project.core.lib.summary.models',
       return_value={'expenses.Expense'})
def test_expenses(mock_models, account_types, expenses):
    actual = collect_summary_data(1999, account_types, 'accounts')

    assert 2 == actual.shape[0]  # rows

    assert 1 == actual.at['Account1', 'id']
    assert 2.5 == actual.at['Account1', 'e_past']
    assert 0.5 == actual.at['Account1', 'e_now']

    assert 2 == actual.at['Account2', 'id']
    assert 2.25 == actual.at['Account2', 'e_past']
    assert 1.25 == actual.at['Account2', 'e_now']


@patch('project.core.lib.summary.models',
       return_value={'expenses.Expense'})
def test_expenses_qs_count(mock_models,
                           account_types, expenses,
                           django_assert_max_num_queries):
    with django_assert_max_num_queries(2):
        [*collect_summary_data(1999, account_types, 'accounts')]


@patch('project.core.lib.summary.models',
       return_value={'savings.Saving'})
def test_savings_for_accounts(mock_models, account_types, savings):
    actual = collect_summary_data(1999, account_types, 'accounts')

    assert 2 == actual.shape[0]  # rows

    assert 1 == actual.at['Account1', 'id']
    assert 1.25 == actual.at['Account1', 's_past']
    assert 3.5 == actual.at['Account1', 's_now']

    assert 2 == actual.at['Account2', 'id']
    assert 0.25 == actual.at['Account2', 's_past']
    assert 2.25 == actual.at['Account2', 's_now']


@patch('project.core.lib.summary.models',
       return_value={'savings.Saving'})
def test_savings_for_savings_with_fees(mock_models, saving_types, savings):
    actual = collect_summary_data(1999, saving_types, 'savings')

    assert 2 == actual.shape[0]  # rows

    assert 1 == actual.at['Saving1', 'id']
    assert 0.25 == actual.at['Saving1', 's_fee_past']
    assert 0.5 == actual.at['Saving1', 's_fee_now']

    assert 2 == actual.at['Saving2', 'id']
    assert 0.0 == actual.at['Saving2', 's_fee_past']
    assert 0.25 == actual.at['Saving2', 's_fee_now']


@patch('project.core.lib.summary.models',
       return_value={'savings.Saving'})
def test_saving_for_savings_with_closed(mock_models):
    s1 = SavingTypeFactory(title='S1')
    s2 = SavingTypeFactory(title='S2', closed=1974)

    SavingFactory(date=date(1999, 1, 1), saving_type=s1)
    SavingFactory(date=date(1999, 1, 1), saving_type=s2)

    actual = collect_summary_data(1999, {'S1': 1}, 'savings')

    assert 1 == actual.shape[0]  # rows


@patch('project.core.lib.summary.models',
       return_value={'savings.Saving'})
def test_savings_qs_count(mock_models,
                          account_types, savings,
                          django_assert_max_num_queries):
    with django_assert_max_num_queries(2):
        [*collect_summary_data(1999, account_types, 'savings')]


@patch('project.core.lib.summary.models',
       return_value={'transactions.Transaction'})
def test_transactions(mock_models, account_types, transactions):
    actual = collect_summary_data(1999, account_types, 'accounts')

    assert 2 == actual.shape[0]  # rows

    assert 1 == actual.at['Account1', 'id']
    assert 1.25 == actual.at['Account1', 'tr_from_past']
    assert 4.5 == actual.at['Account1', 'tr_from_now']
    assert 5.25 == actual.at['Account1', 'tr_to_past']
    assert 3.25 == actual.at['Account1', 'tr_to_now']

    assert 2 == actual.at['Account2', 'id']
    assert 5.25 == actual.at['Account2', 'tr_from_past']
    assert 3.25 == actual.at['Account2', 'tr_from_now']
    assert 1.25 == actual.at['Account2', 'tr_to_past']
    assert 4.5 == actual.at['Account2', 'tr_to_now']


@patch('project.core.lib.summary.models',
       return_value={'transactions.Transaction'})
def test_transactions_qs_count(mock_models,
                               account_types, transactions,
                               django_assert_max_num_queries):
    with django_assert_max_num_queries(4):
        [*collect_summary_data(1999, account_types, 'account')]


@patch('project.core.lib.summary.models',
       return_value={'transactions.SavingClose'})
def test_saving_close_accounts(mock_models, account_types, savings_close):
    actual = collect_summary_data(1999, account_types, 'accounts')

    assert 2 == actual.shape[0]  # rows

    assert 1 == actual.at['Account1', 'id']
    assert 0.25 == actual.at['Account1', 's_close_to_past']
    assert 0.25 == actual.at['Account1', 's_close_to_now']

    assert 2 == actual.at['Account2', 'id']
    assert 0.0 == actual.at['Account2', 's_close_to_past']
    assert 0.0 == actual.at['Account2', 's_close_to_now']


@patch('project.core.lib.summary.models',
       return_value={'transactions.SavingClose'})
def test_saving_close_saving_type(mock_models, savings_close):
    actual = collect_summary_data(1999, {'Saving1': 1}, 'savings')

    assert 1 == actual.shape[0]  # rows

    assert 1 == actual.at['Saving1', 'id']
    assert 0.25 == actual.at['Saving1', 's_close_from_past']
    assert 0.25 == actual.at['Saving1', 's_close_from_now']


@patch('project.core.lib.summary.models',
       return_value={'transactions.SavingClose'})
def test_saving_close_qs_count(mock_models,
                               saving_types, savings_close,
                               django_assert_max_num_queries):
    with django_assert_max_num_queries(4):
        [*collect_summary_data(1999, saving_types, 'savings')]


@patch('project.core.lib.summary.models',
       return_value={'transactions.SavingChange'})
def test_saving_change_accounts(mock_models, savings_change):
    actual = collect_summary_data(1999, {}, 'savings')

    assert isinstance(actual, pd.DataFrame)
    assert actual.empty


@patch('project.core.lib.summary.models',
       return_value={'transactions.SavingChange'})
def test_saving_change_saving_type(mock_models, saving_types, savings_change):
    actual = collect_summary_data(1999, saving_types, 'savings')

    assert 2 == actual.shape[0]  # rows


@patch('project.core.lib.summary.models',
       return_value={'transactions.SavingChange'})
def test_saving_change_qs_count(mock_models,
                                saving_types, savings_change,
                                django_assert_max_num_queries):
    with django_assert_max_num_queries(4):
        [*collect_summary_data(1999, saving_types, 'savings')]


def test_all_qs_count_for_accounts(account_types,
                                   django_assert_max_num_queries):
    with django_assert_max_num_queries(8):
        [*collect_summary_data(1999, account_types, 'account')]


def test_all_qs_count_for_savings(saving_types,
                                  django_assert_max_num_queries):
    with django_assert_max_num_queries(6):
        [*collect_summary_data(1999, saving_types, 'savings')]


def test_pension(pensions):
    actual = collect_summary_data(1999, {'PensionType': 1}, 'pensions')

    assert 1 == actual.shape[0]  # rows

    assert 1 == actual.at['PensionType', 'id']
    assert 3.5 == actual.at['PensionType', 's_past']
    assert 4.5 == actual.at['PensionType', 's_now']
