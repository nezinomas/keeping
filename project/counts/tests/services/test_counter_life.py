from datetime import date

import pytest

from ....core.lib.day_stats import NoPastRecord, PastRecord
from ...services.counter_life import CounterLife
from ..factories import CountFactory, CountTypeFactory

pytestmark = pytest.mark.django_db

TODAY = date(1999, 7, 12)


def test_records_are_keyed_date_and_qty(main_user):
    CountFactory(date=date(1999, 1, 1), quantity=3)

    life = CounterLife.read(main_user, "count-type", TODAY)

    assert life.records == [{"date": date(1999, 1, 1), "qty": 3.0}]


@pytest.mark.parametrize(
    "dates, expect",
    [
        pytest.param(
            [date(1998, 3, 1), date(1998, 12, 20), date(1999, 1, 1)],
            PastRecord(date(1998, 12, 20)),
            id="one_before",
        ),
        pytest.param([date(1999, 1, 1)], NoPastRecord(), id="first_year"),
        pytest.param([], NoPastRecord(), id="no_records"),
    ],
)
def test_earlier_is_the_last_record_before_the_year(dates, expect, main_user):
    CountTypeFactory()
    for day in dates:
        CountFactory(date=day, quantity=1)

    assert CounterLife.read(main_user, "count-type", TODAY).earlier == expect
