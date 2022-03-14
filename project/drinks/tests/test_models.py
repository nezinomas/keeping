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
        user=UserFactory(username='XXX', email='x@x.x')
    )


@pytest.fixture()
def _second_user():
    return DrinkFactory(counter_type='Z', user=UserFactory(username='XXX', email='x@x.x'))


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


def test_drink_related(_different_users):
    actual = Drink.objects.related()

    assert len(actual) == 1
    assert actual[0].user.username == 'bob'


def test_drink_items(_different_users):
    actual = Drink.objects.items()

    assert len(actual) == 1
    assert actual[0].user.username == 'bob'


@patch('project.drinks.managers.DrinkQuerySet.counter_type', 'X')
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


def test_drink_order():
    DrinkFactory(date=date(1999, 1, 1))
    DrinkFactory(date=date(1999, 12, 1))

    actual = list(Drink.objects.year(1999))

    assert str(actual[0]) == '1999-12-01: 1.0'
    assert str(actual[1]) == '1999-01-01: 1.0'


def test_drink_months_consumption(_drinks):
    actual = Drink.objects.sum_by_month(1999)

    # filter per_month key from return list
    actual = [x['per_month'] for x in actual]

    expect = [16.12, 21.43]

    assert expect == pytest.approx(actual, rel=1e-2)


def test_drink_months_quantity_sum(_drinks):
    actual = Drink.objects.sum_by_month(1999)

    # filter sum key from return list
    actual = [x['sum'] for x in actual]

    expect = [1.0, 1.2]

    assert expect == pytest.approx(actual, rel=1e-2)


def test_drink_months_quantity_sum_no_records_for_current_year(_second_user):
    DrinkFactory(date=date(1970, 1, 1), quantity=1.0)
    DrinkFactory(date=date(2000, 1, 1), quantity=1.5)
    DrinkFactory(date=date(1999, 1, 1), quantity=1.5, counter_type=_second_user)

    actual = Drink.objects.sum_by_month(1999)

    expect = []

    assert expect == pytest.approx(actual, rel=1e-2)


def test_drink_months_month_num(_drinks):
    actual = Drink.objects.sum_by_month(1999)

    # filter month key from return list
    actual = [x['month'] for x in actual]

    expect = [1, 2]

    assert expect == actual


def test_drink_months_month_len(_drinks):
    actual = Drink.objects.sum_by_month(1999)

    # filter monthlen key from return list
    actual = [x['monthlen'] for x in actual]

    expect = [31, 28]

    assert expect == list(actual)


@freeze_time('1999-11-01')
def test_drink_days_sum(_second_user):
    DrinkFactory(date=date(1999, 1, 1), quantity=1.0)
    DrinkFactory(date=date(1999, 11, 1), quantity=1.5)
    DrinkFactory(date=date(1999, 11, 1), quantity=111, counter_type=_second_user)

    actual = Drink.objects.drink_day_sum(1999)

    assert actual['qty'] == 1
    assert round(actual['per_day'], 2) == 1.64


@freeze_time('1999-01-03')
def test_drink_days_sum_no_records_for_selected_year(_second_user):
    DrinkFactory(date=date(1999, 1, 1), quantity=1.0)
    DrinkFactory(date=date(1999, 1, 1), quantity=1.0, counter_type=_second_user)
    DrinkFactory(date=date(1999, 11, 1), quantity=1.5)

    actual = Drink.objects.drink_day_sum(1998)

    assert actual == {}


def test_drink_summary():
    DrinkFactory(date=date(1999, 1, 1), quantity=1.0)
    DrinkFactory(date=date(1999, 1, 2), quantity=2.0)
    DrinkFactory(date=date(2000, 1, 1), quantity=1.0)
    DrinkFactory(date=date(2000, 1, 2), quantity=3.0)

    expect = [
        {'year': 1999, 'qty': 1.2, 'per_day': 1.64},
        {'year': 2000, 'qty': 1.6, 'per_day': 2.18},
    ]
    actual = list(Drink.objects.summary())

    assert len(actual) == 2
    assert expect[0] == pytest.approx(actual[0], 0.01)
    assert expect[1] == pytest.approx(actual[1], 0.01)


def test_drink_summary_no_records():
    actual = list(Drink.objects.summary())

    assert not actual


@pytest.mark.parametrize(
    'ml, drink_type, expect',
    [
        (20, 'beer', 50),
        (21, 'beer', 0.1),
        (350, 'beer', 1.75),
        (20, 'wine', 160),
        (21, 'wine', 0.22),
        (350, 'wine', 3.73),
        (20, 'vodka', 800),
        (21, 'vodka', 0.84),
        (350, 'vodka', 14),
    ]
)
def test_drink_recalculate_ml_on_save(ml, drink_type, expect):
    d = DrinkFactory(quantity=ml, option=drink_type)

    assert d.quantity == expect


def test_drink_sum_by_day():
    DrinkFactory(date=date(1999, 1, 1), quantity=1.0)
    DrinkFactory(date=date(1999, 1, 1), quantity=1.5)

    actual = Drink.objects.sum_by_day(1999)

    assert actual[0]['qty'] == 1


@pytest.mark.parametrize(
    'drink_type, quantity, stdav',
    [
        ('beer', 1, 2.5),
        ('beer', 500, 2.5),
        ('wine', 1, 8),
        ('wine', 750, 8),
        ('vodka', 1, 40),
        ('vodka', 1000, 40),
        ('stdav', 1, 1),
        ('stdav', 10, 10),
    ]
)
def test_drink_save_convert_quantity(drink_type, quantity, stdav):
    obj = DrinkFactory(date=date(1999, 1, 1), quantity=quantity, option=drink_type)

    actual = Drink.objects.get(pk=obj.pk)

    assert actual.option == drink_type
    assert actual.quantity == stdav


# ----------------------------------------------------------------------------
#                                                                 Drink Target
# ----------------------------------------------------------------------------
def test_drink_target_fields():
    assert DrinkTarget._meta.get_field('year')
    assert DrinkTarget._meta.get_field('drink_type')
    assert DrinkTarget._meta.get_field('quantity')
    assert DrinkTarget._meta.get_field('user')


def test_drink_target_str():
    actual = DrinkTargetFactory()

    assert str(actual) == '1999: 100.0'


def test_drink_target_related():
    DrinkTargetFactory()
    DrinkTargetFactory(user=UserFactory(username='XXX', email='x@x.x'))

    actual = DrinkTarget.objects.related()

    assert len(actual) == 1
    assert actual[0].user.username == 'bob'


def test_drink_target_items():
    DrinkTargetFactory(year=1999)
    DrinkTargetFactory(year=2000, user=UserFactory(username='XXX', email='x@x.x'))

    actual = DrinkTarget.objects.items()

    assert len(actual) == 1
    assert actual[0].user.username == 'bob'


def test_drink_target_year():
    DrinkTargetFactory(year=1999)
    DrinkTargetFactory(year=1999, user=UserFactory(username='XXX', email='x@x.x'))

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

    actual = DrinkTarget.objects.all()

    assert str(actual[0]) == '1999: 100.0'
    assert str(actual[1]) == '1970: 100.0'


@pytest.mark.parametrize(
    'drink_type, quantity, stdav',
    [
        ('beer', 500, 2.5),
        ('wine', 750, 8),
        ('vodka', 1000, 40),
        ('stdav', 10, 10),
    ]
)
def test_drink_target_save_convert_quantity(drink_type, quantity, stdav):
    obj = DrinkTargetFactory(quantity=quantity, drink_type=drink_type)

    actual = DrinkTarget.objects.get(pk=obj.pk)

    assert actual.drink_type == drink_type
    assert actual.quantity == stdav
