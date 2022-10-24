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
