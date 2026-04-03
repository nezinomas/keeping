from datetime import date

import pytest
from django.core.validators import ValidationError

from ...users.tests.factories import UserFactory
from ..models import Drink, DrinkTarget
from ..services.model_services import DrinkModelService, DrinkTargetModelService
from .factories import DrinkFactory, DrinkTargetFactory

pytestmark = pytest.mark.django_db


@pytest.fixture()
def _drinks(second_user):
    DrinkFactory(date=date(1999, 1, 1), stdav=1.0)
    DrinkFactory(date=date(1999, 1, 1), stdav=1.5)
    DrinkFactory(date=date(1999, 2, 1), stdav=2.0)
    DrinkFactory(date=date(1999, 2, 1), stdav=1.0)

    DrinkFactory(date=date(1999, 2, 1), stdav=100.0, user=second_user)


# ----------------------------------------------------------------------------
#                                                                        Drink
# ----------------------------------------------------------------------------
def test_drink_related(main_user, second_user):
    DrinkFactory()
    DrinkFactory(user=second_user)

    actual = DrinkModelService(main_user).objects

    assert len(actual) == 1
    assert actual[0].user.username == "bob"


def test_drink_items(main_user, second_user):
    DrinkFactory()
    DrinkFactory(user=second_user)

    actual = DrinkModelService(main_user).items()

    assert len(actual) == 1
    assert actual[0].user.username == "bob"


def test_drink_items_different_counters(main_user, second_user):
    DrinkFactory()
    DrinkFactory(user=second_user)

    actual = DrinkModelService(main_user).items()

    assert len(actual) == 1


def test_drink_items_different_counters_default_value(main_user, second_user):
    DrinkFactory()
    DrinkFactory(user=second_user)

    actual = DrinkModelService(main_user).items()

    assert len(actual) == 1


def test_drink_year(main_user, second_user):
    DrinkFactory()
    DrinkFactory(user=second_user)

    actual = list(DrinkModelService(main_user).year(1999))

    assert len(actual) == 1
    assert actual[0].date == date(1999, 1, 1)
    assert actual[0].user.username == "bob"


@pytest.mark.parametrize(
    "drink_type, stdav, expect",
    [
        ("beer", 2.5, 500),
        ("wine", 8, 750),
        ("vodka", 40, 1000),
    ],
)
def test_drink_str_drinks(drink_type, stdav, expect):
    p = DrinkFactory(stdav=stdav, option=drink_type)

    p.full_clean()

    assert str(p) == f"1999-01-01, {drink_type}, {expect}ml"


@pytest.mark.parametrize(
    "drink_type, stdav, expect",
    [
        ("stdav", 1.0, 1.0),
    ],
)
def test_drink_str_stdav(drink_type, stdav, expect):
    p = DrinkFactory(stdav=stdav, option=drink_type)

    p.full_clean()

    assert str(p) == f"1999-01-01, stdav, {expect}"


def test_drink_order(main_user):
    DrinkFactory(date=date(1999, 1, 1))
    DrinkFactory(date=date(1999, 12, 1))

    actual = DrinkModelService(main_user).year(1999)

    assert actual[0].date == date(1999, 12, 1)
    assert actual[1].date == date(1999, 1, 1)


@pytest.mark.parametrize(
    "drink_type, stdav, qty",
    [
        ("beer", [5.5, 2.5], [5.5 / 2.5, 2.5 / 2.5]),
        ("wine", [5.5, 2.5], [5.5 / 8, 2.5 / 8]),
        ("vodka", [5.5, 2.5], [5.5 / 40, 2.5 / 40]),
        ("stdav", [5.5, 2.5], [5.5 / 1, 2.5 / 1]),
    ],
)
def test_drink_sum_by_year(drink_type, stdav, qty, main_user):
    main_user.drink_type = drink_type
    main_user.save()

    DrinkFactory(date=date(1999, 1, 1), stdav=1.0, option="beer")
    DrinkFactory(date=date(1999, 1, 1), stdav=1.5, option="beer")
    DrinkFactory(date=date(2000, 1, 1), stdav=1.5, option="beer")
    DrinkFactory(date=date(1999, 2, 1), stdav=2.0, option="beer")
    DrinkFactory(date=date(1999, 2, 1), stdav=1.0, option="beer")
    DrinkFactory(date=date(2000, 2, 1), stdav=1.0, option="beer")

    actual = DrinkModelService(main_user).sum_by_year()

    # filter per_month key from return list
    actual_stdav = [x["stdav"] for x in actual]
    actual_qty = [x["qty"] for x in actual]

    assert actual_stdav == stdav
    assert actual_qty == qty


@pytest.mark.parametrize(
    "drink_type, stdav, qty",
    [
        ("beer", [2.5, 3.0], [2.5 / 2.5, 3.0 / 2.5]),
        ("wine", [2.5, 3.0], [2.5 / 8, 3.0 / 8]),
        ("vodka", [2.5, 3.0], [2.5 / 40, 3.0 / 40]),
        ("stdav", [2.5, 3.0], [2.5 / 1, 3.0 / 1]),
    ],
)
def test_drink_sum_by_month(drink_type, stdav, qty, main_user):
    main_user.drink_type = drink_type

    DrinkFactory(date=date(1999, 1, 1), stdav=1.0, option="beer")
    DrinkFactory(date=date(1999, 1, 1), stdav=1.5, option="beer")
    DrinkFactory(date=date(2000, 1, 1), stdav=1.5, option="beer")
    DrinkFactory(date=date(1999, 2, 1), stdav=2.0, option="beer")
    DrinkFactory(date=date(1999, 2, 1), stdav=1.0, option="beer")
    DrinkFactory(date=date(2000, 2, 1), stdav=1.0, option="beer")

    actual = DrinkModelService(main_user).sum_by_month(1999)

    # filter per_month key from return list
    actual_stdav = [x["stdav"] for x in actual]
    actual_qty = [round(x["qty"], 4) for x in actual]

    assert actual_stdav == stdav
    assert actual_qty == qty


def test_drink_months_sum_no_records_for_current_year(main_user, second_user):
    DrinkFactory(date=date(1970, 1, 1), stdav=1.0)
    DrinkFactory(date=date(2000, 1, 1), stdav=1.5)
    DrinkFactory(date=date(1999, 1, 1), stdav=1.5, user=second_user)

    actual = DrinkModelService(main_user).sum_by_month(1999)

    assert not actual


@pytest.mark.parametrize(
    "drink_type, stdav, qty",
    [
        ("beer", [2.5], [2.5 / 2.5]),
        ("wine", [2.5], [2.5 / 8]),
        ("vodka", [2.5], [2.5 / 40]),
        ("stdav", [2.5], [2.5 / 1]),
    ],
)
def test_drink_sum_by_day(drink_type, stdav, qty, main_user):
    main_user.drink_type = drink_type

    DrinkFactory(date=date(1999, 1, 1), stdav=1.0, option="beer")
    DrinkFactory(date=date(1999, 1, 1), stdav=1.5, option="beer")
    DrinkFactory(date=date(2000, 1, 1), stdav=1.5, option="beer")
    DrinkFactory(date=date(1999, 2, 1), stdav=2.0, option="beer")
    DrinkFactory(date=date(1999, 2, 1), stdav=1.0, option="beer")
    DrinkFactory(date=date(2000, 2, 1), stdav=1.0, option="beer")

    actual = DrinkModelService(main_user).sum_by_day(1999, 1)

    actual_stdav = [x["stdav"] for x in actual]
    actual_qty = [round(x["qty"], 4) for x in actual]

    assert actual_stdav == stdav
    assert actual_qty == qty


@pytest.mark.parametrize(
    "drink_type, stdav, qty",
    [
        ("beer", [2.5, 3.0], [2.5 / 2.5, 3.0 / 2.5]),
        ("wine", [2.5, 3.0], [2.5 / 8, 3.0 / 8]),
        ("vodka", [2.5, 3.0], [2.5 / 40, 3.0 / 40]),
        ("stdav", [2.5, 3.0], [2.5 / 1, 3.0 / 1]),
    ],
)
def test_drink_sum_by_day_all_months(drink_type, stdav, qty, main_user):
    main_user.drink_type = drink_type
    main_user.save()

    DrinkFactory(date=date(1999, 1, 1), stdav=1.0, option="beer")
    DrinkFactory(date=date(1999, 1, 1), stdav=1.5, option="beer")
    DrinkFactory(date=date(2000, 1, 1), stdav=1.5, option="beer")
    DrinkFactory(date=date(1999, 2, 1), stdav=2.0, option="beer")
    DrinkFactory(date=date(1999, 2, 1), stdav=1.0, option="beer")
    DrinkFactory(date=date(2000, 2, 1), stdav=1.0, option="beer")

    actual = DrinkModelService(main_user).sum_by_day(1999)

    actual_stdav = [x["stdav"] for x in actual]
    actual_qty = [round(x["qty"], 4) for x in actual]

    assert actual_stdav == stdav
    assert actual_qty == qty


# ----------------------------------------------------------------------------
#                                                                 Drink Target
# ----------------------------------------------------------------------------
def test_drink_target_fields():
    assert DrinkTarget._meta.get_field("year")
    assert DrinkTarget._meta.get_field("drink_type")
    assert DrinkTarget._meta.get_field("quantity")
    assert DrinkTarget._meta.get_field("user")


def test_drink_target_str():
    actual = DrinkTargetFactory()

    assert str(actual) == "1999: 100.0"


def test_drink_target_related(main_user):
    DrinkTargetFactory()
    DrinkTargetFactory(user=UserFactory(username="XXX", email="x@x.x"))

    actual = DrinkTargetModelService(main_user).objects

    assert len(actual) == 1
    assert actual[0].user.username == "bob"


def test_drink_target_items(main_user):
    DrinkTargetFactory(year=1999)
    DrinkTargetFactory(year=2000, user=UserFactory(username="XXX", email="x@x.x"))

    actual = DrinkTargetModelService(main_user).items()

    assert len(actual) == 1
    assert actual[0].user.username == "bob"


def test_drink_target_year(main_user):
    DrinkTargetFactory(year=1999, quantity=1, drink_type="beer")
    DrinkTargetFactory(year=1999, user=UserFactory(username="XXX", email="x@x.x"))

    actual = DrinkTargetModelService(main_user).year(1999)

    assert len(actual) == 1
    assert actual[0].year == 1999
    assert round(actual[0].quantity, 3) == 0.005
    assert actual[0].user.username == "bob"


def test_drink_target_year_positive():
    actual = DrinkTargetFactory.build(year=-2000)

    try:
        actual.full_clean()
    except ValidationError as e:
        assert "year" in e.message_dict


@pytest.mark.xfail(raises=Exception)
def test_drink_target_year_unique():
    DrinkTargetFactory(year=1999)
    DrinkTargetFactory(year=1999)


def test_drink_target_ordering():
    DrinkTargetFactory(year=1970)
    DrinkTargetFactory(year=1999)

    actual = DrinkTarget.objects.all()

    assert str(actual[0]) == "1999: 100.0"
    assert str(actual[1]) == "1970: 100.0"


@pytest.mark.parametrize(
    "drink_type, quantity, stdav",
    [
        ("beer", 500, 2.5),
        ("wine", 750, 8),
        ("vodka", 1000, 40),
        ("stdav", 10, 10),
    ],
)
def test_drink_target_save_convert_quantity(drink_type, quantity, stdav):
    obj = DrinkTargetFactory(quantity=quantity, drink_type=drink_type)

    actual = DrinkTarget.objects.get(pk=obj.pk)

    assert actual.drink_type == drink_type
    assert actual.quantity == stdav
