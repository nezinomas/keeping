import pytest

from ...core.tests.utils import equal_list_of_dictionaries as assert_
from ..models import SavingType

pytestmark = pytest.mark.django_db


def test_savings_only(savings):
    expect = [{
        'title': 'Saving1',
        'past_amount': 1.25,
        'past_fee': 0.25,
        'incomes': 4.75,
        'fees': 0.75,
        'invested': 4.0,
    }, {
        'title': 'Saving2',
        'past_amount': 0.25,
        'past_fee': 0.0,
        'incomes': 2.50,
        'fees': 0.25,
        'invested': 2.25,
    }]

    actual = list(SavingType.objects.balance_year(1999))

    assert_(expect, actual)


def test_savings_change_only(savings_change):
    expect = [{
        'title': 'Saving1',
        'past_amount': -2.25,
        'past_fee': 0.15,
        'incomes': -3.50,
        'fees': 0.20,
        'invested': -3.70,
    }, {
        'title': 'Saving2',
        'past_amount': 2.25,
        'past_fee': 0.15,
        'incomes': 3.50,
        'fees': 0.20,
        'invested': 3.30,
    }]

    actual = list(SavingType.objects.balance_year(1999))

    assert_(expect, actual)


def test_savings_cloce_only(savings_close):
    expect = [{
        'title': 'Saving1',
        'past_amount': -0.25,
        'past_fee': 0.0,
        'incomes': -0.5,
        'fees': 0.0,
        'invested': -0.5,
    }]

    actual = list(SavingType.objects.balance_year(1999))

    assert_(expect, actual)


def test_savings_year_now(savings, savings_close, savings_change):
    expect = [{
        'title': 'Saving1',
        'past_amount': -1.25,
        'past_fee': 0.40,
        'incomes': 0.75,
        'fees': 0.95,
        'invested': -0.20,
    }, {
        'title': 'Saving2',
        'past_amount': 2.50,
        'past_fee': 0.15,
        'incomes': 6.00,
        'fees': 0.45,
        'invested': 5.55,
    }]

    actual = list(SavingType.objects.balance_year(1999))

    assert_(expect, actual)


def test_savings_year_past(savings, savings_close, savings_change):
    expect = [{
        'title': 'Saving1',
        'past_amount': 0.00,
        'past_fee': 0.0,
        'incomes': -1.25,
        'fees': 0.40,
        'invested': -1.65,
    }, {
        'title': 'Saving2',
        'past_amount': 0.00,
        'past_fee': 0.00,
        'incomes': 2.50,
        'fees': 0.15,
        'invested': 2.35,
    }]

    actual = list(SavingType.objects.balance_year(1970))

    assert_(expect, actual)


def test_savings_empty():
    actual = list(SavingType.objects.balance_year(1))

    assert actual == []
