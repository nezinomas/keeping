from datetime import date
from unittest.mock import patch

import pytest

from ...core.tests.utils import view_for
from .. import services
from ..services.detailed.providers import DetailedDataProvider
from ..services.expenses import ExpenseServiceData
from ..services.forecast.providers import ForecastDataProvider
from ..services.index.providers import IndexDataProvider
from ..services.month.providers import MonthDataProvider
from ..views import TabBalance, TabFunds, TabOverview

pytestmark = pytest.mark.django_db

TODAY = date(1999, 1, 1)


def _detailed_service(user):
    # the provider is built first and raises for the same user
    with patch(f"{services.detailed.presenters.__name__}.DetailedDataProvider"):
        return services.detailed.load_service(user, "income")


def _index_service(user):
    # IndexDataProvider reads the year too: patched, the service's own read is alone
    with patch(f"{services.index.presenters.__name__}.IndexDataProvider"):
        return services.index.load_service(user, TODAY)


def _tab_view(view_class):
    def read(rf, user):
        # the services read the year too: patched, the view's own read is alone
        with (
            patch.object(services.index, "load_service"),
            patch.object(services.expenses, "load_service"),
        ):
            return view_for(rf, user, view_class).get_context_data()

    return read


def _month_service(user):
    with patch(f"{services.month.presenters.__name__}.MonthDataProvider"):
        return services.month.load_service(user, TODAY)


@pytest.mark.parametrize(
    "read",
    [
        pytest.param(_tab_view(TabOverview), id="overview_tab"),
        pytest.param(_tab_view(TabFunds), id="funds_tab"),
        pytest.param(_tab_view(TabBalance), id="balance_tab"),
        pytest.param(
            lambda rf, u: services.forecast.load_service(u, TODAY),
            id="forecast_service",
        ),
        pytest.param(lambda rf, u: ForecastDataProvider(u), id="forecast_provider"),
        pytest.param(lambda rf, u: _detailed_service(u), id="detailed_service"),
        pytest.param(lambda rf, u: DetailedDataProvider(u), id="detailed_provider"),
        pytest.param(lambda rf, u: _index_service(u), id="index_service"),
        pytest.param(lambda rf, u: IndexDataProvider(u), id="index_provider"),
        pytest.param(lambda rf, u: ExpenseServiceData(u), id="expenses_data"),
        pytest.param(lambda rf, u: _month_service(u), id="month_service"),
        pytest.param(lambda rf, u: MonthDataProvider(u), id="month_provider"),
    ],
)
def test_a_user_with_no_year_raises(main_user, rf, read):
    main_user.year = None

    with pytest.raises(ValueError, match="has no year"):
        read(rf, main_user)
