import pytest

from ...users.models import User
from ..services import history as T

pytestmark = pytest.mark.django_db


@pytest.mark.freeze_time('2000-01-01')
def test_years():
    qs = [{'year': 1998, 'qty': 1}]
    actual = T.HistoryService(qs).years

    assert actual == [1998, 1999, 2000]


@pytest.mark.parametrize(
    'drink_type, qty, expect',
    [
        ('beer', 1, [0.01, 0.0]),
        ('wine', 1, [0.01, 0.0]),
        ('vodka', 1, [0.01, 0.0]),
        ('stdav', 1, [0.01, 0.0]),
    ]
)
@pytest.mark.freeze_time('2000-01-01')
def test_pure_alcohol(drink_type, qty, expect, get_user):
    get_user.drink_type = drink_type

    qs = [{'year': 1999, 'qty': qty}]
    print(User.objects.values())
    actual = T.HistoryService(qs).alcohol

    assert actual == expect


@pytest.mark.parametrize(
    'drink_type, qty, expect',
    [
        ('beer', 912.5, [500.0, 0.0]),
        ('wine', 2_920, [750.0, 0.0]),
        ('vodka', 14_600, [1000.0, 0.0]),
        ('stdav', 365, [10.0, 0.0]),
    ]
)
@pytest.mark.freeze_time('2000-01-01')
def test_per_day(drink_type, qty, expect, get_user):
    get_user.drink_type = drink_type

    qs = [{'year': 1999, 'qty': qty}]
    print(User.objects.values())
    actual = T.HistoryService(qs).per_day

    assert actual == expect


@pytest.mark.parametrize(
    'drink_type, qty, expect',
    [
        ('beer', 912.5, [365.0, 0.0]),
        ('wine', 2_920, [365.0, 0.0]),
        ('vodka', 14_600, [365.0, 0.0]),
        ('stdav', 365, [365.0, 0.0]),
    ]
)
@pytest.mark.freeze_time('2000-01-01')
def test_quantity(drink_type, qty, expect, get_user):
    get_user.drink_type = drink_type

    qs = [{'year': 1999, 'qty': qty}]
    print(User.objects.values())
    actual = T.HistoryService(qs).quantity

    assert actual == expect
