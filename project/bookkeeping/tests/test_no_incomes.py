import pytest

from ..lib.no_incomes import NoIncomes as T


@pytest.fixture()
def _avg_type_expenses():
    return {'E3': 3.0, 'E2': 2.0, 'E1': 1.0}


def test_no_incomes_summary(_avg_type_expenses):
    expect = [
        {'money_fund': 7.0, 'money_fund_pension': 8.0, 'label': 'money'},
        {'money_fund': 1.4, 'money_fund_pension': 1.6, 'label': 'no_cut'},
        {'money_fund': 3.5, 'money_fund_pension': 4.0, 'label': 'cut'},
    ]

    actual = T(
        money=3.0, fund=4.0, pension=1.0,
        avg_expenses=5.0, cut_sum=3.0,
    )

    assert expect == actual.summary


def test_no_incomes_summary_no_used_list(_avg_type_expenses):
    expect = [
        {'money_fund': 7.0, 'money_fund_pension': 8.0, 'label': 'money'},
        {'money_fund': 1.4, 'money_fund_pension': 1.6, 'label': 'no_cut'},
        {'money_fund': 1.4, 'money_fund_pension': 1.6, 'label': 'cut'},
    ]

    actual = T(
        money=3.0, fund=4.0, pension=1.0,
        avg_expenses=5.0, cut_sum=None
    )

    assert expect == actual.summary


def test_no_incomes_summary_no_used_no_keys_in_avg_type_expenses(_avg_type_expenses):
    expect = [
        {'money_fund': 7.0, 'money_fund_pension': 8.0, 'label': 'money'},
        {'money_fund': 1.4, 'money_fund_pension': 1.6, 'label': 'no_cut'},
        {'money_fund': 1.4, 'money_fund_pension': 1.6, 'label': 'cut'},
    ]

    actual = T(
        money=3.0, fund=4.0, pension=1.0,
        avg_expenses=5.0, cut_sum=None
    )

    assert expect == actual.summary


def test_no_incomes_summary_expenses_zero(_avg_type_expenses):
    expect = [
        {'money_fund': 7.0, 'money_fund_pension': 8.0, 'label': 'money'},
        {'money_fund': 0.0, 'money_fund_pension': 0.0, 'label': 'no_cut'},
        {'money_fund': 0.0, 'money_fund_pension': 0.0, 'label': 'cut'},
    ]

    actual = T(
        money=3.0, fund=4.0, pension=1.0,
        avg_expenses=0, cut_sum=None
    )

    assert expect == actual.summary


def test_no_incomes_summary_avg_type_expenses_none():
    expect = [
        {'money_fund': 7.0, 'money_fund_pension': 8.0, 'label': 'money'},
        {'money_fund': 0.0, 'money_fund_pension': 0.0, 'label': 'no_cut'},
        {'money_fund': 0.0, 'money_fund_pension': 0.0, 'label': 'cut'},
    ]

    actual = T(
        money=3.0, fund=4.0, pension=1.0,
        avg_expenses=0, cut_sum=None
    )

    assert expect == actual.summary
