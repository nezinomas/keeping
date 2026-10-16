from datetime import date, datetime
from zoneinfo import ZoneInfo

import time_machine

from ...mixins.kwargs import TodayMixin


def test_today_is_the_local_date():
    # 01:00 in Vilnius is still 2026 in UTC
    with time_machine.travel(
        datetime(2027, 1, 1, 1, 0, tzinfo=ZoneInfo("Europe/Vilnius"))
    ):
        assert TodayMixin().today == date(2027, 1, 1)
