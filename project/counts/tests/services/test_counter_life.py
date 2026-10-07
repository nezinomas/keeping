from datetime import date, datetime

import pytest
import time_machine

from ....core.lib.day_stats import Stats
from ...services.counter_life import CounterLife
from ..factories import CountFactory, CountTypeFactory

pytestmark = pytest.mark.django_db


@time_machine.travel(datetime(1999, 7, 12))
def test_records_are_keyed_date_and_qty(main_user):
    CountFactory(date=date(1999, 1, 1), quantity=3)

    life = CounterLife.read(main_user, "count-type")

    assert life.records == [{"date": date(1999, 1, 1), "qty": 3.0}]


@time_machine.travel(datetime(1999, 7, 12))
def test_records_reach_stats_as_qty(main_user):
    CountTypeFactory()
    CountFactory(date=date(1999, 1, 1), quantity=3)

    stats = Stats(data=CounterLife.read(main_user, "count-type").records)

    assert stats._df["qty"][0] == 3.0
