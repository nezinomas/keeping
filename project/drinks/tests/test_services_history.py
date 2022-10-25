import pytest

from ..services import history as T

pytestmark = pytest.mark.django_db


@pytest.mark.freeze_time('2000-01-01')
def test_years():
    qs = [{'year': 1998, 'qty': 1, 'stdav': 2.5}]
    actual = T.HistoryService(qs).years

    assert actual == [1998, 1999, 2000]


@pytest.mark.parametrize(
    'drink_type, qty, stdav, expect',
    [
        ('beer', 1, 2.5, [0.025, 0.0]),
        ('wine', 1, 8, [0.08, 0.0]),
        ('vodka', 1, 40, [0.4, 0.0]),
        ('stdav', 1, 10, [0.1, 0.0]),
    ]
)
@pytest.mark.freeze_time('2000-01-01')
def test_pure_alcohol(drink_type, qty, stdav, expect, get_user):
    get_user.drink_type = drink_type

    qs = [{'year': 1999, 'qty': qty, 'stdav': stdav}]

    actual = T.HistoryService(qs).alcohol

    assert actual == expect


@pytest.mark.parametrize(
    'drink_type, qty, stdav, expect',
    [
        ('beer', 365, 912.5, [500.0, 0.0]),
        ('wine', 365, 2_920, [750.0, 0.0]),
        ('vodka', 365, 14_600, [1000.0, 0.0]),
        ('stdav', 365, 365, [10.0, 0.0]),
    ]
)
@pytest.mark.freeze_time('2000-01-01')
def test_per_day(drink_type, qty, stdav, expect, get_user):
    get_user.drink_type = drink_type

    qs = [{'year': 1999, 'qty': qty, 'stdav': stdav}]

    actual = T.HistoryService(qs).per_day

    assert actual == expect


@pytest.mark.parametrize(
    'drink_type, qty, stdav, expect',
    [
        ('beer', 365, 912.5, [500.0, 182_500]),
        ('wine', 365, 2_920, [750.0, 273_750]),
        ('vodka', 365, 14_600, [1000.0, 365_000]),
        ('stdav', 365, 365, [10.0, 3_650]),
    ]
)
@pytest.mark.freeze_time('2000-01-01')
def test_per_day_adjusted_for_current_year(drink_type, qty, stdav, expect, get_user):
    get_user.drink_type = drink_type

    qs = [
        {'year': 1999, 'qty': qty, 'stdav': stdav},
        {'year': 2000, 'qty': qty, 'stdav': stdav},
    ]

    actual = T.HistoryService(qs).per_day

    assert actual == expect


@pytest.mark.parametrize(
    'drink_type, qty, stdav, expect',
    [
        ('beer', 365, 912.5, [365.0, 0.0]),
        ('wine', 365, 2_920, [365.0, 0.0]),
        ('vodka', 365, 14_600, [365.0, 0.0]),
        ('stdav', 365, 365, [365.0, 0.0]),
    ]
)
@pytest.mark.freeze_time('2000-01-01')
def test_quantity(drink_type, qty, stdav, expect, get_user):
    get_user.drink_type = drink_type

    qs = [{'year': 1999, 'qty': qty, 'stdav': stdav}]

    actual = T.HistoryService(qs).quantity

    assert actual == expect
