from datetime import date

import pytest
from django.contrib.auth.models import AnonymousUser

from ...services.model_services import DrinkModelService, DrinkTargetModelService
from ..factories import DrinkFactory, DrinkTargetFactory


def test_drink_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        DrinkModelService(user=None)


def test_drink_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        DrinkModelService(user=anon)


@pytest.mark.django_db
def test_drink_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    DrinkModelService(user=main_user)


@pytest.mark.django_db
def test_years_are_the_years_holding_a_drink_oldest_first(main_user):
    DrinkFactory(date=date(2005, 3, 1))
    DrinkFactory(date=date(1999, 1, 1))
    DrinkFactory(date=date(1999, 6, 1))

    assert DrinkModelService(user=main_user).years() == [1999, 2005]


@pytest.mark.django_db
def test_years_without_records_is_empty_not_none(main_user):
    assert DrinkModelService(user=main_user).years() == []


def test_drink_target_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        DrinkTargetModelService(user=None)


def test_drink_target_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        DrinkTargetModelService(user=anon)


@pytest.mark.django_db
def test_drink_target_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    DrinkTargetModelService(user=main_user)


@pytest.mark.django_db
def test_get_target_no_data(main_user):
    target_dto = DrinkTargetModelService(user=main_user).get_target(1999)

    assert not target_dto.has_data
    assert target_dto.target_id == 0
    assert target_dto.qty == 0.0


@pytest.mark.django_db
def test_get_target_with_data(main_user):
    target = DrinkTargetFactory(user=main_user, year=1999, quantity=500)
    target_dto = DrinkTargetModelService(user=main_user).get_target(1999)

    assert target_dto.has_data
    assert target_dto.target_id == target.id
    assert target_dto.qty == 500.0  # 500ml beer = 2.5 stdav


# -------------------------------------------------------------------------------------
#                                        a target is re-expressed in the viewing unit
# -------------------------------------------------------------------------------------
@pytest.mark.django_db
@pytest.mark.parametrize(
    "viewing, target_type, ml, expect_qty",
    [
        # a 500 ml beer target is 2.5 std av; every row below is that same
        # amount, read in a different drink type
        ("beer", "beer", 500, 500.0),
        ("wine", "beer", 500, 234.375),
        ("vodka", "beer", 500, 62.5),
        # 750 ml of wine is 8 std av
        ("beer", "wine", 750, 1600.0),
        ("wine", "wine", 750, 750.0),
        # Std Av is canonical: read as itself, not multiplied out to a volume
        ("stdav", "beer", 500, 2.5),
    ],
)
def test_target_is_read_in_the_users_drink_type(
    viewing, target_type, ml, expect_qty, main_user
):
    main_user.drink_type = viewing
    main_user.save()

    DrinkTargetFactory(user=main_user, year=1999, drink_type=target_type, quantity=ml)

    actual = DrinkTargetModelService(user=main_user).get_target(1999)

    assert round(actual.qty, 4) == expect_qty


@pytest.mark.django_db
def test_target_amount_is_a_drink_quantity(main_user):
    DrinkTargetFactory(user=main_user, year=1999, quantity=500)

    actual = DrinkTargetModelService(user=main_user).get_target(1999).amount

    assert actual.is_volume is True
    assert actual.drink_type == "beer"
    assert actual.stdav == 2.5
    assert actual.display == "500 ml"


@pytest.mark.django_db
def test_get_target_only_the_users_own(main_user, second_user):
    DrinkTargetFactory(user=second_user, year=1999, quantity=500)

    assert DrinkTargetModelService(user=main_user).get_target(1999).has_data is False


@pytest.mark.django_db
def test_year_returns_plain_rows_without_annotations(main_user):
    """The unit conversion left SQL; `year()` is just a filtered queryset now."""
    DrinkTargetFactory(user=main_user, year=1999, quantity=500)

    row = DrinkTargetModelService(user=main_user).year(1999).first()

    assert row.quantity == 2.5  # stored in std av
    assert not hasattr(row, "qty")
