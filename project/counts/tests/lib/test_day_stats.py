import tempfile
from datetime import date

import pytest
from django.test import override_settings

from ....core.lib.day_stats import Stats
from ...services.model_services import CountModelService
from ..factories import CountFactory


@pytest.fixture(name="data_db")
@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def fixture_data_db():
    CountFactory(date=date(1998, 1, 1), quantity=1.0)
    CountFactory(date=date(1999, 12, 3), quantity=1.0)
    CountFactory(date=date(1999, 2, 1), quantity=1.0)
    CountFactory(date=date(1999, 2, 1), quantity=1.0)
    CountFactory(date=date(1999, 1, 15), quantity=1.0)
    CountFactory(date=date(1999, 1, 15), quantity=1.0)
    CountFactory(date=date(1999, 1, 8), quantity=1.0)
    CountFactory(date=date(2000, 1, 8), quantity=1.0)


@pytest.mark.django_db
def test_stats_months_aggregation_from_db(main_user, data_db):
    year = 1999
    qs = CountModelService(main_user).sum_by_day(year=year, count_type="count-type")
    actual = Stats(year=year, data=qs).months_stats()
    expect = [3.0, 2.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
    assert actual == expect
