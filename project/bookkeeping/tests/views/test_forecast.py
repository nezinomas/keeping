from datetime import date

import pytest

from ....core.tests.utils import view_for
from ....expenses.tests.factories import ExpenseFactory
from ....incomes.tests.factories import IncomeFactory
from ...views import TabOverview

pytestmark = pytest.mark.django_db


def test_the_forecast_has_no_route_of_its_own(client_logged):
    assert client_logged.get("/bookkeeping/forecast/").status_code == 404


def test_forecast_reads_the_month_of_the_views_today(rf, main_user):
    IncomeFactory(price=1000, date=date(1999, 1, 5))
    ExpenseFactory(price=200, date=date(1999, 1, 6))
    ExpenseFactory(price=300, date=date(1999, 2, 6))
    view = view_for(rf, main_user, TabOverview)
    # apart from the clock, so a read of the clock shows
    view.today = date(1999, 2, 10)

    assert view.get_context_data()["forecast"]["data"] == [0, -1500, -1500]
