from datetime import date

import pandas as pd
import pytest
from mock import Mock, patch
from pandas.api.types import is_numeric_dtype

from ...savings.factories import SavingFactory, SavingTypeFactory
from ..lib.summary import (AccountsBalanceModels, ModelsAbstract,
                           PensionsBalanceModels, SavingsBalanceModels,
                           collect_summary_data)

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
    'borrow_past', 'borrow_now',
    'borrow_return_past', 'borrow_return_now',
    'lent_past', 'lent_now',
    'lent_return_past', 'lent_return_now',
]


@pytest.fixture()
def _account_types():
    return {'Account1': 1, 'Account2': 2}


@pytest.fixture()
def _saving_types():
    return {'Saving1': 1, 'Saving2': 2}


@patch('project.core.lib.summary.AccountsBalanceModels.models',
       return_value={'incomes.Income'})
def test_no_accounts_model_not_exists(mock_models):
    actual = collect_summary_data(1999, [], AccountsBalanceModels)

    assert isinstance(actual, pd.DataFrame)
    assert actual.empty


@patch('project.core.lib.summary.AccountsBalanceModels.models',
       return_value={'incomes.Income'})
def test_model_not_exists(mock_models, _account_types):
    actual = collect_summary_data(1999, _account_types, AccountsBalanceModels)

    assert len(columns) == actual.shape[1]  # columns

    for col in columns:
        assert col in actual.columns


@patch('project.core.lib.summary.AccountsBalanceModels.models',
       return_value={'incomes.Income'})
@patch('django.apps.apps.get_model')
def test_model_dont_have_summary_method(mock_get, mock_models):
    model = Mock()
    model.objects.summary.side_effect = AttributeError('no summary')
    model.objects.summary_to.side_effect = AttributeError('no summary_to')
    model.objects.summary_from.side_effect = AttributeError('no summary_from')

    mock_get.return_value = model

    actual = collect_summary_data(1999, {}, AccountsBalanceModels)

    assert isinstance(actual, pd.DataFrame)
    assert actual.empty


@patch('project.core.lib.summary.AccountsBalanceModels.models',
       return_value={'incomes.Income'})
@patch('django.apps.apps.get_model')
def test_model_summary_without_title(mock_get, mock_models):
    model = Mock()
    model.objects.summary.return_value = [{'x': 'x'}]
    model.objects.summary_to.side_effect = AttributeError('no summary_to')
    model.objects.summary_from.side_effect = AttributeError('no summary_from')

    mock_get.return_value = model
    actual = collect_summary_data(1999, {}, AccountsBalanceModels)

    assert isinstance(actual, pd.DataFrame)
    assert actual.empty


@patch('project.core.lib.summary.AccountsBalanceModels.models',
       return_value={'incomes.Income'})
def test_incomes_df_accounts(mock_models, _account_types, incomes):
    actual = collect_summary_data(1999, _account_types, AccountsBalanceModels)

    assert isinstance(actual, pd.DataFrame)

    assert actual.shape[0] == 2  # rows

    assert actual.at['Account1', 'id'] == 1
    assert actual.at['Account1', 'i_past'] == 5.25
    assert actual.at['Account1', 'i_now'] == 3.25

    assert actual.at['Account2', 'id'] == 2
    assert actual.at['Account2', 'i_past'] == 4.5
    assert actual.at['Account2', 'i_now'] == 3.5


@patch('project.core.lib.summary.AccountsBalanceModels.models',
       return_value={'incomes.Income'})
def test_incomes_df_accounts_only_one_account(mock_models, incomes):
    actual = collect_summary_data(1999, {'Account1': 1}, AccountsBalanceModels)

    assert isinstance(actual, pd.DataFrame)

    assert actual.shape[0] == 1  # rows

    assert actual.at['Account1', 'id'] == 1
    assert actual.at['Account1', 'i_past'] == 5.25
    assert actual.at['Account1', 'i_now'] == 3.25


@patch('project.core.lib.summary.AccountsBalanceModels.models',
       return_value={'incomes.Income'})
def test_df_dtypes(mock_models, _account_types, incomes):
    actual = collect_summary_data(1999, _account_types, AccountsBalanceModels)

    for col in columns:
        assert is_numeric_dtype(actual[col])


@patch('project.core.lib.summary.AccountsBalanceModels.models',
       return_value={'incomes.Income'})
def test_df_have_nan(mock_models, _account_types, incomes):
    actual = collect_summary_data(1999, _account_types, AccountsBalanceModels)

    for col in columns:
        assert not actual[col].isnull().values.any()


@patch('project.core.lib.summary.AccountsBalanceModels.models',
       return_value={'incomes.Income'})
def test_incomes_df_savings(mock_models, incomes):
    actual = collect_summary_data(1999, {}, AccountsBalanceModels)

    assert isinstance(actual, pd.DataFrame)
    assert actual.empty


@patch('project.core.lib.summary.AccountsBalanceModels.models',
       return_value={'incomes.Income'})
def test_incomes_qs_count(mock_models,
                          _account_types, incomes,
                          django_assert_max_num_queries):
    with django_assert_max_num_queries(2):
        list(collect_summary_data(1999, _account_types, AccountsBalanceModels))


@patch('project.core.lib.summary.AccountsBalanceModels.models',
       return_value={'expenses.Expense'})
def test_expenses(mock_models, _account_types, expenses):
    actual = collect_summary_data(1999, _account_types, AccountsBalanceModels)

    assert actual.shape[0] == 2  # rows

    assert actual.at['Account1', 'id'] == 1
    assert actual.at['Account1', 'e_past'] == 2.5
    assert actual.at['Account1', 'e_now'] == 0.5

    assert actual.at['Account2', 'id'] == 2
    assert actual.at['Account2', 'e_past'] == 2.25
    assert actual.at['Account2', 'e_now'] == 1.25


@patch('project.core.lib.summary.AccountsBalanceModels.models',
       return_value={'expenses.Expense'})
def test_expenses_qs_count(mock_models,
                           _account_types, expenses,
                           django_assert_max_num_queries):
    with django_assert_max_num_queries(2):
        list(collect_summary_data(1999, _account_types, AccountsBalanceModels))


@patch('project.core.lib.summary.AccountsBalanceModels.models',
       return_value={'savings.Saving'})
def test_savings_for_accounts(mock_models, _account_types, savings):
    actual = collect_summary_data(1999, _account_types, AccountsBalanceModels)

    assert actual.shape[0] == 2  # rows

    assert actual.at['Account1', 'id'] == 1
    assert actual.at['Account1', 's_past'] == 1.25
    assert actual.at['Account1', 's_now'] == 3.5

    assert actual.at['Account2', 'id'] == 2
    assert actual.at['Account2', 's_past'] == 0.25
    assert actual.at['Account2', 's_now'] == 2.25


@patch('project.core.lib.summary.SavingsBalanceModels.models',
       return_value={'savings.Saving'})
def test_savings_for_savings_with_fees(mock_models, _saving_types, savings):
    actual = collect_summary_data(1999, _saving_types, SavingsBalanceModels)

    assert actual.shape[0] == 2  # rows

    assert actual.at['Saving1', 'id'] == 1
    assert actual.at['Saving1', 's_fee_past'] == 0.25
    assert actual.at['Saving1', 's_fee_now'] == 0.5

    assert actual.at['Saving2', 'id'] == 2
    assert actual.at['Saving2', 's_fee_past'] == 0.0
    assert actual.at['Saving2', 's_fee_now'] == 0.25


@patch('project.core.lib.summary.SavingsBalanceModels.models',
       return_value={'savings.Saving'})
def test_saving_for_savings_with_closed(mock_models):
    s1 = SavingTypeFactory(title='S1')
    s2 = SavingTypeFactory(title='S2', closed=1974)

    SavingFactory(date=date(1999, 1, 1), saving_type=s1)
    SavingFactory(date=date(1999, 1, 1), saving_type=s2)

    actual = collect_summary_data(1999, {'S1': 1}, SavingsBalanceModels)

    assert actual.shape[0] == 1  # rows


@patch('project.core.lib.summary.SavingsBalanceModels.models',
       return_value={'savings.Saving'})
def test_savings_qs_count(mock_models,
                          _account_types, savings,
                          django_assert_max_num_queries):
    with django_assert_max_num_queries(2):
        list(collect_summary_data(1999, _account_types, SavingsBalanceModels))


@patch('project.core.lib.summary.AccountsBalanceModels.models',
       return_value={'transactions.Transaction'})
def test_transactions(mock_models, _account_types, transactions):
    actual = collect_summary_data(1999, _account_types, AccountsBalanceModels)

    assert actual.shape[0] == 2  # rows

    assert actual.at['Account1', 'id'] == 1
    assert actual.at['Account1', 'tr_from_past'] == 1.25
    assert actual.at['Account1', 'tr_from_now'] == 4.5
    assert actual.at['Account1', 'tr_to_past'] == 5.25
    assert actual.at['Account1', 'tr_to_now'] == 3.25

    assert actual.at['Account2', 'id'] == 2
    assert actual.at['Account2', 'tr_from_past'] == 5.25
    assert actual.at['Account2', 'tr_from_now'] == 3.25
    assert actual.at['Account2', 'tr_to_past'] == 1.25
    assert actual.at['Account2', 'tr_to_now'] == 4.5


@patch('project.core.lib.summary.AccountsBalanceModels.models',
       return_value={'transactions.Transaction'})
def test_transactions_qs_count(mock_models,
                               _account_types, transactions,
                               django_assert_max_num_queries):
    with django_assert_max_num_queries(4):
        list(collect_summary_data(1999, _account_types, AccountsBalanceModels))


@patch('project.core.lib.summary.AccountsBalanceModels.models',
       return_value={'transactions.SavingClose'})
def test_saving_close_accounts(mock_models, _account_types, savings_close):
    actual = collect_summary_data(1999, _account_types, AccountsBalanceModels)

    assert actual.shape[0] == 2  # rows

    assert actual.at['Account1', 'id'] == 1
    assert actual.at['Account1', 's_close_to_past'] == 0.25
    assert actual.at['Account1', 's_close_to_now'] == 0.25

    assert actual.at['Account2', 'id'] == 2
    assert actual.at['Account2', 's_close_to_past'] == 0.0
    assert actual.at['Account2', 's_close_to_now'] == 0.0


@patch('project.core.lib.summary.SavingsBalanceModels.models',
       return_value={'transactions.SavingClose'})
def test_saving_close_saving_type(mock_models, savings_close):
    actual = collect_summary_data(1999, {'Saving1': 1}, SavingsBalanceModels)

    assert actual.shape[0] == 1 # rows

    assert actual.at['Saving1', 'id'] == 1
    assert actual.at['Saving1', 's_close_from_past'] == 0.25
    assert actual.at['Saving1', 's_close_from_now'] == 0.25


@patch('project.core.lib.summary.SavingsBalanceModels.models',
       return_value={'transactions.SavingClose'})
def test_saving_close_qs_count(mock_models,
                               _saving_types, savings_close,
                               django_assert_max_num_queries):
    with django_assert_max_num_queries(4):
        list(collect_summary_data(1999, _saving_types, SavingsBalanceModels))


@patch('project.core.lib.summary.SavingsBalanceModels.models',
       return_value={'transactions.SavingChange'})
def test_saving_change_accounts(mock_models, savings_change):
    actual = collect_summary_data(1999, {}, SavingsBalanceModels)

    assert isinstance(actual, pd.DataFrame)
    assert actual.empty


@patch('project.core.lib.summary.SavingsBalanceModels.models',
       return_value={'transactions.SavingChange'})
def test_saving_change_saving_type(mock_models, _saving_types, savings_change):
    actual = collect_summary_data(1999, _saving_types, SavingsBalanceModels)

    assert actual.shape[0] == 2 # rows


@patch('project.core.lib.summary.SavingsBalanceModels.models',
       return_value={'transactions.SavingChange'})
def test_saving_change_qs_count(mock_models,
                                _saving_types, savings_change,
                                django_assert_max_num_queries):
    with django_assert_max_num_queries(4):
        list(collect_summary_data(1999, _saving_types, SavingsBalanceModels))


def test_all_qs_count_for_accounts(_account_types,
                                   django_assert_max_num_queries):
    with django_assert_max_num_queries(12):
        list(collect_summary_data(1999, _account_types, AccountsBalanceModels))


def test_all_qs_count_for_savings(_saving_types,
                                  django_assert_max_num_queries):
    with django_assert_max_num_queries(6):
        list(collect_summary_data(1999, _saving_types, SavingsBalanceModels))


def test_pension(pensions):
    actual = collect_summary_data(1999, {'PensionType': 1}, PensionsBalanceModels)

    assert actual.shape[0] == 1  # rows

    assert actual.at['PensionType', 'id'] == 1
    assert actual.at['PensionType', 's_past'] == 3.5
    assert actual.at['PensionType', 's_now'] == 4.5


@patch.multiple(ModelsAbstract, __abstractmethods__=set())
def test_models_abstract_class():
    ModelsAbstract().models()


@patch('project.core.lib.summary.AccountsBalanceModels.models',
       return_value={'debts.Borrow'})
def test_borrow_for_accounts(mock_models, borrow_fixture):
    _account_types = {'A1': 1, 'A2': 2}
    actual = collect_summary_data(1999, _account_types, AccountsBalanceModels)

    assert actual.shape[0] == 2  # rows

    assert actual.at['A1', 'id'] == 1
    assert actual.at['A1', 'borrow_past'] == 9.0
    assert actual.at['A1', 'borrow_now'] == 3.0

    assert actual.at['A2', 'id'] == 2
    assert actual.at['A2', 'borrow_past'] == 0.0
    assert actual.at['A2', 'borrow_now'] == 3.1


@patch('project.core.lib.summary.AccountsBalanceModels.models',
       return_value={'debts.BorrowReturn'})
def test_borrow_return_for_accounts(mock_models, borrow_return_fixture):
    _account_types = {'A1': 1, 'A2': 2}
    actual = collect_summary_data(1999, _account_types, AccountsBalanceModels)

    print(actual)
    assert actual.shape[0] == 2  # rows

    assert actual.at['A1', 'id'] == 1
    assert actual.at['A1', 'borrow_return_past'] == 8.0
    assert actual.at['A1', 'borrow_return_now'] == 2.0

    assert actual.at['A2', 'id'] == 2
    assert actual.at['A2', 'borrow_return_past'] == 0.0
    assert actual.at['A2', 'borrow_return_now'] == 1.6


@patch('project.core.lib.summary.AccountsBalanceModels.models',
       return_value={'debts.Lent'})
def test_lent_for_accounts(mock_models, lent_fixture):
    _account_types = {'A1': 1, 'A2': 2}
    actual = collect_summary_data(1999, _account_types, AccountsBalanceModels)

    assert actual.shape[0] == 2  # rows

    assert actual.at['A1', 'id'] == 1
    assert actual.at['A1', 'lent_past'] == 9.0
    assert actual.at['A1', 'lent_now'] == 3.0

    assert actual.at['A2', 'id'] == 2
    assert actual.at['A2', 'lent_past'] == 0.0
    assert actual.at['A2', 'lent_now'] == 3.1


@patch('project.core.lib.summary.AccountsBalanceModels.models',
       return_value={'debts.LentReturn'})
def test_lent_return_for_accounts(mock_models, lent_return_fixture):
    _account_types = {'A1': 1, 'A2': 2}
    actual = collect_summary_data(1999, _account_types, AccountsBalanceModels)

    print(actual)
    assert actual.shape[0] == 2  # rows

    assert actual.at['A1', 'id'] == 1
    assert actual.at['A1', 'lent_return_past'] == 8.0
    assert actual.at['A1', 'lent_return_now'] == 2.0

    assert actual.at['A2', 'id'] == 2
    assert actual.at['A2', 'lent_return_past'] == 0.0
    assert actual.at['A2', 'lent_return_now'] == 1.6
