from datetime import date

import pytest
from django.core.validators import ValidationError

from ...users.factories import UserFactory
from ..factories import DrinkFactory, DrinkTargetFactory
from ..models import Drink, DrinkTarget

pytestmark = pytest.mark.django_db


@pytest.fixture()
def _drinks(second_user):
    DrinkFactory(date=date(1999, 1, 1), quantity=1.0)
    DrinkFactory(date=date(1999, 1, 1), quantity=1.5)
    DrinkFactory(date=date(1999, 2, 1), quantity=2.0)
    DrinkFactory(date=date(1999, 2, 1), quantity=1.0)

    DrinkFactory(
        date=date(1999, 2, 1),
        quantity=100.0,
        user=second_user
    )

# ----------------------------------------------------------------------------
#                                                                        Drink
# ----------------------------------------------------------------------------
def test_drink_related(second_user):
    DrinkFactory()
    DrinkFactory(user=second_user)

    actual = Drink.objects.related()

    assert len(actual) == 1
    assert actual[0].user.username == 'bob'


def test_drink_items(second_user):
    DrinkFactory()
    DrinkFactory(user=second_user)

    actual = Drink.objects.items()

    assert len(actual) == 1
    assert actual[0].user.username == 'bob'


def test_drink_items_different_counters(second_user):
    DrinkFactory()
    DrinkFactory(user=second_user)

    actual = Drink.objects.items()

    assert len(actual) == 1


def test_drink_items_different_counters_default_value(second_user):
    DrinkFactory()
    DrinkFactory(user=second_user)

    actual = Drink.objects.items()

    assert len(actual) == 1


def test_drink_year(second_user):
    DrinkFactory()
    DrinkFactory(user=second_user)

    actual = list(Drink.objects.year(1999))

    assert len(actual) == 1
    assert actual[0].date == date(1999, 1, 1)
    assert actual[0].user.username == 'bob'


@pytest.mark.parametrize(
    'user_drink_type, drink_type, expect',
    [
        ('beer', 'beer', 1.0),
        ('wine', 'beer', 0.31),
        ('vodka', 'beer', 0.06),
    ]
)
def test_drink_str(user_drink_type, drink_type, expect, main_user):
    main_user.drink_type = user_drink_type
    p = DrinkFactory(quantity=1, option=drink_type)

    p.full_clean()

    assert str(p) == f'1999-01-01: {expect}'


def test_drink_order():
    DrinkFactory(date=date(1999, 1, 1))
    DrinkFactory(date=date(1999, 12, 1))

    actual = list(Drink.objects.year(1999))

    assert str(actual[0]) == '1999-12-01: 1.0'
    assert str(actual[1]) == '1999-01-01: 1.0'


@pytest.mark.parametrize(
    'drink_type, stdav, qty',
    [
        ('beer', [13.75, 6.25], [5.5, 2.5]),
        ('wine', [13.75, 6.25], [1.72, 0.78]),
        ('vodka', [13.75, 6.25], [0.34, 0.16]),
        ('stdav', [13.75, 6.25], [13.75, 6.25]),
    ]
)
def test_drink_sum_by_year(drink_type, stdav, qty, main_user):
    main_user.drink_type = drink_type

    DrinkFactory(date=date(1999, 1, 1), quantity=1.0, option='beer')
    DrinkFactory(date=date(1999, 1, 1), quantity=1.5, option='beer')
    DrinkFactory(date=date(2000, 1, 1), quantity=1.5, option='beer')
    DrinkFactory(date=date(1999, 2, 1), quantity=2.0, option='beer')
    DrinkFactory(date=date(1999, 2, 1), quantity=1.0, option='beer')
    DrinkFactory(date=date(2000, 2, 1), quantity=1.0, option='beer')

    actual = Drink.objects.sum_by_year()

    # filter per_month key from return list
    actual_stdav = [x['stdav'] for x in actual]
    actual_qty = [round(x['qty'], 2) for x in actual]

    assert actual_stdav == stdav
    assert actual_qty == qty


@pytest.mark.parametrize(
    'drink_type, stdav, qty',
    [
        ('beer', [6.25, 7.5], [2.5, 3.0]),
        ('wine', [6.25, 7.5], [0.78, 0.94]),
        ('vodka', [6.25, 7.5], [0.16, 0.19]),
        ('stdav', [6.25, 7.5], [6.25, 7.5]),
    ]
)
def test_drink_sum_by_month(drink_type, stdav, qty, main_user):
    main_user.drink_type = drink_type

    DrinkFactory(date=date(1999, 1, 1), quantity=1.0, option='beer')
    DrinkFactory(date=date(1999, 1, 1), quantity=1.5, option='beer')
    DrinkFactory(date=date(2000, 1, 1), quantity=1.5, option='beer')
    DrinkFactory(date=date(1999, 2, 1), quantity=2.0, option='beer')
    DrinkFactory(date=date(1999, 2, 1), quantity=1.0, option='beer')
    DrinkFactory(date=date(2000, 2, 1), quantity=1.0, option='beer')

    actual = Drink.objects.sum_by_month(1999)

    # filter per_month key from return list
    actual_stdav = [x['stdav'] for x in actual]
    actual_qty = [round(x['qty'], 2) for x in actual]

    assert actual_stdav == stdav
    assert actual_qty == qty


def test_drink_months_sum_no_records_for_current_year(second_user):
    DrinkFactory(date=date(1970, 1, 1), quantity=1.0)
    DrinkFactory(date=date(2000, 1, 1), quantity=1.5)
    DrinkFactory(date=date(1999, 1, 1), quantity=1.5, user=second_user)

    actual = Drink.objects.sum_by_month(1999)

    assert not actual


@pytest.mark.parametrize(
    'drink_type, stdav, qty',
    [
        ('beer', [6.25], [2.5]),
        ('wine', [6.25], [0.78]),
        ('vodka', [6.25], [0.16]),
        ('stdav', [6.25], [6.25]),
    ]
)
def test_drink_sum_by_day(drink_type, stdav, qty, main_user):
    main_user.drink_type = drink_type

    DrinkFactory(date=date(1999, 1, 1), quantity=1.0, option='beer')
    DrinkFactory(date=date(1999, 1, 1), quantity=1.5, option='beer')
    DrinkFactory(date=date(2000, 1, 1), quantity=1.5, option='beer')
    DrinkFactory(date=date(1999, 2, 1), quantity=2.0, option='beer')
    DrinkFactory(date=date(1999, 2, 1), quantity=1.0, option='beer')
    DrinkFactory(date=date(2000, 2, 1), quantity=1.0, option='beer')

    actual = Drink.objects.sum_by_day(1999, 1)

    actual_stdav = [x['stdav'] for x in actual]
    actual_qty = [round(x['qty'], 2) for x in actual]

    assert actual_stdav == stdav
    assert actual_qty == qty


@pytest.mark.parametrize(
    'drink_type, stdav, qty',
    [
        ('beer', [6.25, 7.5], [2.5, 3.0]),
        ('wine', [6.25, 7.5], [0.78, 0.94]),
        ('vodka', [6.25, 7.5], [0.16, 0.19]),
        ('stdav', [6.25, 7.5], [6.25, 7.5]),
    ]
)
def test_drink_sum_by_day_all_months(drink_type, stdav, qty, main_user):
    main_user.drink_type = drink_type

    DrinkFactory(date=date(1999, 1, 1), quantity=1.0, option='beer')
    DrinkFactory(date=date(1999, 1, 1), quantity=1.5, option='beer')
    DrinkFactory(date=date(2000, 1, 1), quantity=1.5, option='beer')
    DrinkFactory(date=date(1999, 2, 1), quantity=2.0, option='beer')
    DrinkFactory(date=date(1999, 2, 1), quantity=1.0, option='beer')
    DrinkFactory(date=date(2000, 2, 1), quantity=1.0, option='beer')

    actual = Drink.objects.sum_by_day(1999)

    actual_stdav = [x['stdav'] for x in actual]
    actual_qty = [round(x['qty'], 2) for x in actual]

    assert actual_stdav == stdav
    assert actual_qty == qty


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

    assert round(d.quantity, 2) == expect


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
    DrinkTargetFactory(year=1999, quantity=1, drink_type='beer')
    DrinkTargetFactory(year=1999, user=UserFactory(username='XXX', email='x@x.x'))

    actual = DrinkTarget.objects.year(1999)

    assert len(actual) == 1
    assert actual[0].year == 1999
    assert round(actual[0].quantity, 3) == 0.005
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
