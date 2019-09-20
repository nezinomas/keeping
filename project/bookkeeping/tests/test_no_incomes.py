import pytest

from ..lib.no_incomes import NoIncomes as T


@pytest.fixture()
def _avg_type_expenses():
    return {'E3': 3.0, 'E2': 2.0, 'E1': 1.0}


def test_no_incomes_summary(_avg_type_expenses):
    expect = [
        {'not_use': 0, 'money_fund': 7.0, 'money_fund_pension': 8.0},
        {'not_use': 0, 'money_fund': 1.4, 'money_fund_pension': 1.6},
        {'not_use': 3.0, 'money_fund': 3.5, 'money_fund_pension': 4.0},
    ]

    actual = T(
        money=3.0, fund=4.0, pension=1.0,
        avg_expenses=5.0, avg_type_expenses=_avg_type_expenses,
        not_use=['E1', 'E2']
    ).summary

    assert expect == actual


def test_no_incomes_summary_no_used_list(_avg_type_expenses):
    expect = [
        {'not_use': 0, 'money_fund': 7.0, 'money_fund_pension': 8.0},
        {'not_use': 0, 'money_fund': 1.4, 'money_fund_pension': 1.6},
        {'not_use': 0, 'money_fund': 1.4, 'money_fund_pension': 1.6},
    ]

    actual = T(
        money=3.0, fund=4.0, pension=1.0,
        avg_expenses=5.0, avg_type_expenses=_avg_type_expenses,
        not_use=None
    ).summary

    assert expect == actual


def test_no_incomes_summary_no_used_no_keys_in_avg_type_expenses(_avg_type_expenses):
    expect = [
        {'not_use': 0, 'money_fund': 7.0, 'money_fund_pension': 8.0},
        {'not_use': 0, 'money_fund': 1.4, 'money_fund_pension': 1.6},
        {'not_use': 0, 'money_fund': 1.4, 'money_fund_pension': 1.6},
    ]

    actual = T(
        money=3.0, fund=4.0, pension=1.0,
        avg_expenses=5.0, avg_type_expenses=_avg_type_expenses,
        not_use=['x', 'y']
    ).summary

    assert expect == actual


def test_no_incomes_summary_expenses_zero(_avg_type_expenses):
    expect = [
        {'not_use': 0, 'money_fund': 7.0, 'money_fund_pension': 8.0},
        {'not_use': 0, 'money_fund': 0.0, 'money_fund_pension': 0.0},
        {'not_use': 0, 'money_fund': 0.0, 'money_fund_pension': 0.0},
    ]

    actual = T(
        money=3.0, fund=4.0, pension=1.0,
        avg_expenses=0, avg_type_expenses=_avg_type_expenses,
        not_use=None
    ).summary

    assert expect == actual
