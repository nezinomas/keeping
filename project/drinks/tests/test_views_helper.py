from datetime import date
from types import SimpleNamespace

import pytest
from project.drinks.lib.drinks_stats import DrinkStats

from ..factories import DrinkFactory
from ..services import index_tab as T

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    'past, current, expect',
    [
        (
            date(1998, 1, 1),
            None,
            {'date': date(1998, 1, 1), 'delta': 367}
        ),
        (
            None,
            date(1999, 1, 1),
            {'date': date(1999, 1, 1), 'delta': 2}
        ),
        (
            date(1998, 1, 1),
            date(1999, 1, 1),
            {'date': date(1999, 1, 1), 'delta': 2}
        ),
        (None, None, {}),
    ]
)
@pytest.mark.freeze_time('1999-01-03')
def test_dry_days(past, current, expect):
    DrinkFactory()

    actual = \
        T.RenderContext(
            drink_stats=DrinkStats(),
            latest_past_date=past,
            latest_current_date=current
        ).tbl_dry_days()

    assert actual == expect


def test_dry_days_no_records():
    actual = \
        T.RenderContext(
            drink_stats=DrinkStats()
        ).tbl_dry_days()

    assert not actual


def test_target_label_position_between():
    actual = \
        T.RenderContext(
            drink_stats=DrinkStats()
        )._target_label_position(avg=55, target=50)

    assert actual == 15


def test_target_label_position_higher():
    actual = \
        T.RenderContext(
            drink_stats=DrinkStats()
        )._target_label_position(avg=55, target=500)

    assert actual == -5


def test_target_label_position_lower():
    actual = \
        T.RenderContext(
            drink_stats=DrinkStats()
        )._target_label_position(avg=500, target=50)

    assert actual == -5


def test_avg_label_position_between():
    actual = \
        T.RenderContext(
            drink_stats=DrinkStats()
        )._avg_label_position(avg=50, target=55)

    assert actual == 15


def test_avg_label_position_higher():
    actual = \
        T.RenderContext(
            drink_stats=DrinkStats()
        )._avg_label_position(avg=55, target=500)

    assert actual == -5


def test_avg_label_position_lower():
    actual = \
        T.RenderContext(
            drink_stats=DrinkStats()
        )._avg_label_position(avg=500, target=50)

    assert actual == -5


@pytest.mark.freeze_time('2019-10-10')
def test_std_av():
    actual = \
        T.RenderContext(
            drink_stats=DrinkStats()
        )._std_av(2019, 273.5)

    expect = [
        {
            'title': 'Alus, 0.5L',
            'total': 273.5,
            'per_day': 0.97,
            'per_week': 6.67,
            'per_month': 27.35
        }, {
            'title': 'Vynas, 0.75L',
            'total': 85.47,
            'per_day': 0.3,
            'per_week': 2.08,
            'per_month': 8.55
        }, {
            'title': 'Degtinė, 1L',
            'total': 17.09,
            'per_day': 0.06,
            'per_week': 0.42,
            'per_month': 1.71
        }, {
            'title': 'Std Av',
            'total': 683.75,
            'per_day': 2.42,
            'per_week': 16.68,
            'per_month': 68.38
        }
    ]

    assert len(actual) == 4

    for i, row in enumerate(actual):
        for k, v in row.items():
            if k == 'title':
                assert expect[i][k] == v
            else:
                assert expect[i][k] == round(v, 2)


@pytest.mark.freeze_time('2019-10-10')
def test_std_av_past_recods():
    actual = \
        T.RenderContext(
            drink_stats=DrinkStats()
        )._std_av(1999, 273.5)

    expect = [
        {
            'title': 'Alus, 0.5L',
            'total': 273.5,
            'per_day': 0.75,
            'per_week': 5.26,
            'per_month': 22.79
        }, {
            'title': 'Vynas, 0.75L',
            'total': 85.47,
            'per_day': 0.23,
            'per_week': 1.64,
            'per_month': 7.12
        }, {
            'title': 'Degtinė, 1L',
            'total': 17.09,
            'per_day': 0.05,
            'per_week': 0.33,
            'per_month': 1.42
        }, {
            'title': 'Std Av',
            'total': 683.75,
            'per_day': 1.87,
            'per_week': 13.15,
            'per_month': 56.98
        }
    ]

    assert len(actual) == 4

    for i, row in enumerate(actual):
        for k, v in row.items():
            if k == 'title':
                assert expect[i][k] == v
            else:
                assert expect[i][k] == round(v, 2)


@pytest.mark.parametrize(
    'drink_type, qty, expect',
    [
        ('beer', 4, 0.1),
        ('wine', 1.25, 0.1),
        ('vodka', 0.25, 0.1),
        ('stdav', 10, 0.1),
    ]
)
def test_tbl_alcohol(drink_type, qty, expect, get_user):
    get_user.drink_type = drink_type

    stats = SimpleNamespace(
        year=1999,
        qty_of_year=qty,
        per_day_of_year=0.0,
    )

    actual = T.RenderContext(drink_stats=stats).tbl_alcohol()

    assert actual['liters'] == expect
