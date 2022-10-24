from datetime import date

import freezegun
import pytest

from ..factories import DrinkFactory
from ..lib import views_helper as T

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
@freezegun.freeze_time('1999-01-03')
def test_dry_days(fake_request, past, current, expect):
    DrinkFactory()

    actual = T.RenderContext(
        fake_request,
        1999,
        None,
        latest_past_date=past,
        latest_current_date=current)._dry_days()

    assert actual == expect


def test_dry_days_no_records(fake_request):
    actual = T.RenderContext(fake_request, 1999, None)._dry_days()

    assert not actual


def test_target_label_position_between(fake_request):
    actual = T.RenderContext(fake_request, 1999, None)._target_label_position(avg=55, target=50)

    assert actual == 15


def test_target_label_position_higher(fake_request):
    actual = T.RenderContext(fake_request, 1999, None)._target_label_position(avg=55, target=500)

    assert actual == -5


def test_target_label_position_lower(fake_request):
    actual = T.RenderContext(fake_request, 1999, None)._target_label_position(avg=500, target=50)

    assert actual == -5


def test_avg_label_position_between(fake_request):
    actual = T.RenderContext(fake_request, 1999, None)._avg_label_position(avg=50, target=55)

    assert actual == 15


def test_avg_label_position_higher(fake_request):
    actual = T.RenderContext(fake_request, 1999, None)._avg_label_position(avg=55, target=500)

    assert actual == -5


def test_avg_label_position_lower(fake_request):
    actual = T.RenderContext(fake_request, 1999, None)._avg_label_position(avg=500, target=50)

    assert actual == -5


@pytest.mark.freeze_time('2019-10-10')
def test_std_av(fake_request):
    actual = T.RenderContext(fake_request, 1999, None).std_av(2019, 273.5)

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
def test_std_av_past_recods(fake_request):
    actual = T.RenderContext(fake_request, 1999, None).std_av(1999, 273.5)

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
