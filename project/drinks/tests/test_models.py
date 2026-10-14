from datetime import date
from operator import attrgetter, methodcaller

import pytest
from django.core.validators import ValidationError
from django.db import IntegrityError, transaction

from ...users.tests.factories import UserFactory
from ..models import DrinkTarget
from ..services.model_services import DrinkModelService, DrinkTargetModelService
from .factories import DrinkFactory, DrinkTargetFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "factory, service, read, mine, theirs",
    [
        (DrinkFactory, DrinkModelService, attrgetter("objects"), {}, {}),
        (DrinkFactory, DrinkModelService, methodcaller("items"), {}, {}),
        (DrinkFactory, DrinkModelService, methodcaller("year", 1999), {}, {}),
        (DrinkTargetFactory, DrinkTargetModelService, attrgetter("objects"), {}, {}),
        (
            DrinkTargetFactory,
            DrinkTargetModelService,
            methodcaller("items"),
            {"year": 1999},
            {"year": 2000},
        ),
    ],
)
def test_service_reads_only_own_rows(
    factory, service, read, mine, theirs, main_user, second_user
):
    factory(**mine)
    factory(user=second_user, **theirs)

    actual = read(service(main_user))

    assert len(actual) == 1
    assert actual[0].user.username == "bob"


def test_drink_year(main_user):
    DrinkFactory()

    actual = list(DrinkModelService(main_user).year(1999))

    assert len(actual) == 1
    assert actual[0].date == date(1999, 1, 1)


@pytest.mark.parametrize(
    "drink_type, stdav, expect",
    [
        ("beer", 2.5, "500ml"),
        ("wine", 8, "750ml"),
        ("vodka", 40, "1000ml"),
        ("stdav", 1.0, "1.0"),
    ],
)
def test_drink_str(drink_type, stdav, expect):
    p = DrinkFactory(stdav=stdav, option=drink_type)

    p.full_clean()

    assert str(p) == f"1999-01-01, {drink_type}, {expect}"


def test_drink_order(main_user):
    DrinkFactory(date=date(1999, 1, 1))
    DrinkFactory(date=date(1999, 12, 1))

    actual = DrinkModelService(main_user).year(1999)

    assert actual[0].date == date(1999, 12, 1)
    assert actual[1].date == date(1999, 1, 1)


@pytest.mark.parametrize(
    "drink_type, servings",
    [("beer", 2.5), ("wine", 8), ("vodka", 40), ("stdav", 1)],
)
@pytest.mark.parametrize(
    "read, stdav",
    [
        (methodcaller("sum_by_year"), [5.5, 2.5]),
        (methodcaller("sum_by_month", 1999), [2.5, 3.0]),
        (methodcaller("sum_by_day", 1999), [2.5, 3.0]),
    ],
)
def test_drink_sums(read, stdav, drink_type, servings, main_user):
    main_user.drink_type = drink_type
    main_user.save()

    DrinkFactory(date=date(1999, 1, 1), stdav=1.0, option="beer")
    DrinkFactory(date=date(1999, 1, 1), stdav=1.5, option="beer")
    DrinkFactory(date=date(2000, 1, 1), stdav=1.5, option="beer")
    DrinkFactory(date=date(1999, 2, 1), stdav=2.0, option="beer")
    DrinkFactory(date=date(1999, 2, 1), stdav=1.0, option="beer")
    DrinkFactory(date=date(2000, 2, 1), stdav=1.0, option="beer")

    actual = read(DrinkModelService(main_user))

    assert [x["stdav"] for x in actual] == stdav
    assert [x["qty"] for x in actual] == pytest.approx([x / servings for x in stdav])


def test_drink_months_sum_no_records_for_current_year(main_user, second_user):
    DrinkFactory(date=date(1970, 1, 1), stdav=1.0)
    DrinkFactory(date=date(2000, 1, 1), stdav=1.5)
    DrinkFactory(date=date(1999, 1, 1), stdav=1.5, user=second_user)

    actual = DrinkModelService(main_user).sum_by_month(1999)

    assert not actual


def test_drink_target_str():
    actual = DrinkTargetFactory()

    assert str(actual) == "1999: 100.0"


def test_drink_target_year(main_user):
    DrinkTargetFactory(year=1999, quantity=1, drink_type="beer")
    DrinkTargetFactory(year=1999, user=UserFactory(username="XXX", email="x@x.x"))

    actual = DrinkTargetModelService(main_user).year(1999)

    assert len(actual) == 1
    assert actual[0].year == 1999
    assert round(actual[0].quantity, 3) == 0.005
    assert actual[0].user.username == "bob"


def test_drink_target_year_positive(main_user):
    # a saved user, so year is the only invalid field - an unsaved one makes
    # full_clean report `user` too and masks a year rule that stopped firing
    actual = DrinkTargetFactory.build(year=-2000, user=main_user)

    with pytest.raises(ValidationError) as error:
        actual.full_clean()

    assert list(error.value.message_dict) == ["year"]


def test_drink_target_year_unique(main_user):
    # one target per year per user; the constraint holding is the passing
    # behaviour, so assert it rather than marking the test xfail
    DrinkTargetFactory(year=1999, user=main_user)

    with pytest.raises(IntegrityError), transaction.atomic():
        DrinkTargetFactory(year=1999, user=main_user)


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
