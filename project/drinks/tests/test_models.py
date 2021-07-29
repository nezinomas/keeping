from datetime import date

import pytest
from django.core.validators import ValidationError
from freezegun import freeze_time
from mock import patch

from ...users.factories import UserFactory
from ..factories import DrinkFactory, DrinkTargetFactory
from ..models import Drink, DrinkTarget

pytestmark = pytest.mark.django_db


@pytest.fixture()
def _drinks():
    DrinkFactory(date=date(1999, 1, 1), quantity=1.0)
    DrinkFactory(date=date(1999, 1, 1), quantity=1.5)
    DrinkFactory(date=date(1999, 2, 1), quantity=2.0)
    DrinkFactory(date=date(1999, 2, 1), quantity=1.0)

    DrinkFactory(
        date=date(1999, 2, 1),
        quantity=100.0,
        counter_type='Z',
        user=UserFactory(username='XXX')
    )


@pytest.fixture()
def _second_user():
    return DrinkFactory(counter_type='Z', user=UserFactory(username='XXX'))


@pytest.fixture()
def _different_users(_second_user):
    DrinkFactory()
    DrinkFactory(counter_type=_second_user)


# ----------------------------------------------------------------------------
#                                                                        Drink
# ----------------------------------------------------------------------------
def test_drink_str():
    actual = DrinkFactory.build()

    assert str(actual) == '1999-01-01: 1'


@patch('project.drinks.models.DrinkQuerySet.App_name', 'Counter Type')
def test_drink_related(_different_users):
    actual = Drink.objects.related()

    assert len(actual) == 1
    assert actual[0].user.username == 'bob'


@patch('project.drinks.models.DrinkQuerySet.App_name', 'Counter Type')
def test_drink_items(_different_users):
    actual = Drink.objects.items()

    assert len(actual) == 1
    assert actual[0].user.username == 'bob'


@patch('project.drinks.models.DrinkQuerySet.App_name', 'X')
def test_drink_items_different_counters():
    DrinkFactory(counter_type='x')
    DrinkFactory(counter_type='z')

    actual = Drink.objects.items()

    assert len(actual) == 1


def test_drink_items_different_counters_default_value():
    DrinkFactory(counter_type='drinks')
    DrinkFactory(counter_type='z')

    actual = Drink.objects.items()

    assert len(actual) == 1


@patch('project.drinks.models.DrinkQuerySet.App_name', 'Counter Type')
def test_drink_year(_different_users):
    actual = list(Drink.objects.year(1999))

    assert len(actual) == 1
    assert actual[0].date == date(1999, 1, 1)
    assert actual[0].user.username == 'bob'


def test_drink_quantity_float():
    p = DrinkFactory(quantity=0.5)

    p.full_clean()

    assert str(p) == '1999-01-01: 0.5'


def test_drink_quantity_int():
    p = DrinkFactory(quantity=5)

    p.full_clean()

    assert str(p) == '1999-01-01: 5.0'


@patch('project.drinks.models.DrinkQuerySet.App_name', 'Counter Type')
def test_drink_order():
    DrinkFactory(date=date(1999, 1, 1))
    DrinkFactory(date=date(1999, 12, 1))

    actual = list(Drink.objects.year(1999))

    assert str(actual[0]) == '1999-12-01: 1.0'
    assert str(actual[1]) == '1999-01-01: 1.0'


@patch('project.drinks.models.DrinkQuerySet.App_name', 'Counter Type')
def test_drink_months_consumption(_drinks):
    actual = Drink.objects.sum_by_month(1999)

    # filter per_month key from return list
    actual = [x['per_month'] for x in actual]

    expect = [40.32, 53.57]

    assert expect == pytest.approx(actual, rel=1e-2)


@patch('project.drinks.models.DrinkQuerySet.App_name', 'Counter Type')
def test_drink_months_quantity_sum(_drinks):
    actual = Drink.objects.sum_by_month(1999)

    # filter sum key from return list
    actual = [x['sum'] for x in actual]

    expect = [2.5, 3.0]

    assert expect == pytest.approx(actual, rel=1e-2)


def test_drink_months_quantity_sum_no_records_for_current_year(_second_user):
    DrinkFactory(date=date(1970, 1, 1), quantity=1.0)
    DrinkFactory(date=date(2000, 1, 1), quantity=1.5)
    DrinkFactory(date=date(1999, 1, 1), quantity=1.5, counter_type=_second_user)

    actual = Drink.objects.sum_by_month(1999)

    expect = []

    assert expect == pytest.approx(actual, rel=1e-2)


@patch('project.drinks.models.DrinkQuerySet.App_name', 'Counter Type')
def test_drink_months_month_num(_drinks):
    actual = Drink.objects.sum_by_month(1999)

    # filter month key from return list
    actual = [x['month'] for x in actual]

    expect = [1, 2]

    assert expect == actual


@patch('project.drinks.models.DrinkQuerySet.App_name', 'Counter Type')
def test_drink_months_month_len(_drinks):
    actual = Drink.objects.sum_by_month(1999)

    # filter monthlen key from return list
    actual = [x['monthlen'] for x in actual]

    expect = [31, 28]

    assert expect == list(actual)


@freeze_time('1999-11-01')
@patch('project.drinks.models.DrinkQuerySet.App_name', 'Counter Type')
def test_drink_days_sum(_second_user):
    DrinkFactory(date=date(1999, 1, 1), quantity=1.0)
    DrinkFactory(date=date(1999, 11, 1), quantity=1.5)
    DrinkFactory(date=date(1999, 11, 1), quantity=111, counter_type=_second_user)

    actual = Drink.objects.drink_day_sum(1999)

    assert actual['qty'] == 2.5
    assert round(actual['per_day'], 2) == 4.1


@freeze_time('1999-01-03')
def test_drink_days_sum_no_records_for_selected_year(_second_user):
    DrinkFactory(date=date(1999, 1, 1), quantity=1.0)
    DrinkFactory(date=date(1999, 1, 1), quantity=1.0, counter_type=_second_user)
    DrinkFactory(date=date(1999, 11, 1), quantity=1.5)

    actual = Drink.objects.drink_day_sum(1998)

    assert actual == {}


@patch('project.drinks.models.DrinkQuerySet.App_name', 'Counter Type')
def test_drink_summary():
    DrinkFactory(date=date(1999, 1, 1), quantity=1.0)
    DrinkFactory(date=date(1999, 1, 2), quantity=2.0)
    DrinkFactory(date=date(2000, 1, 1), quantity=1.0)
    DrinkFactory(date=date(2000, 1, 2), quantity=3.0)

    expect = [
        {'year': 1999, 'qty': 3.0, 'per_day': 4.11},
        {'year': 2000, 'qty': 4.0, 'per_day': 5.46},
    ]
    actual = list(Drink.objects.summary())

    assert len(actual) == 2
    assert expect[0] == pytest.approx(actual[0], 0.01)
    assert expect[1] == pytest.approx(actual[1], 0.001)


def test_drink_summary_no_records():
    actual = list(Drink.objects.summary())

    assert actual == []


@pytest.mark.parametrize(
    'value, expect',
    [(20, 20), (21, 0.04), (350, 0.7)]
)
def test_drink_recalculate_ml_on_save(value, expect):
    d = DrinkFactory(quantity=value)

    assert d.quantity == expect


# ----------------------------------------------------------------------------
#                                                                 Drink Target
# ----------------------------------------------------------------------------
def test_drink_target_str():
    actual = DrinkTargetFactory.build()

    assert str(actual) == '1999: 100'


def test_drink_target_related():
    DrinkTargetFactory()
    DrinkTargetFactory(user=UserFactory(username='XXX'))

    actual = DrinkTarget.objects.related()

    assert len(actual) == 1
    assert actual[0].user.username == 'bob'


def test_drink_target_items():
    DrinkTargetFactory(year=1999)
    DrinkTargetFactory(year=2000, user=UserFactory(username='XXX'))

    actual = DrinkTarget.objects.items()

    assert len(actual) == 1
    assert actual[0].user.username == 'bob'


def test_drink_target_year():
    DrinkTargetFactory(year=1999)
    DrinkTargetFactory(year=1999, user=UserFactory(username='XXX'))

    actual = list(DrinkTarget.objects.year(1999))

    assert len(actual) == 1
    assert actual[0].year == 1999
    assert actual[0].user.username == 'bob'


def test_drink_target_year_positive():
    actual = DrinkTargetFactory.build(year=-2000)

    try:
        actual.full_clean()
    except ValidationError as e:
        assert 'year' in e.message_dict


@pytest.mark.xfail(raises=Exception)
def test_drink_target_year_unique():
    DrinkTargetFactory(year=1999)
    DrinkTargetFactory(year=1999)


def test_drink_target_ordering():
    DrinkTargetFactory(year=1970)
    DrinkTargetFactory(year=1999)

    actual = list(DrinkTarget.objects.all())

    assert str(actual[0]) == '1999: 100'
    assert str(actual[1]) == '1970: 100'
