from datetime import date

import pytest

from ....core.tests.utils import count_queries
from ....incomes.tests.factories import IncomeFactory
from ....savings.models import SavingType
from ....savings.tests.factories import SavingTypeFactory
from ...lib.no_incomes import load_service as no_incomes_load_service
from ...services.forecast.presenters import load_service as forecast_load_service
from ...services.month.presenters import load_service as month_load_service
from ..helper import quiet_build
from ..signals.helpers import buy

pytestmark = pytest.mark.django_db

ACCOUNT = SavingType.FeeSource.ACCOUNT
INVESTMENT = SavingType.FeeSource.INVESTMENT


def _purchase(fee_source, title="Fund", day=date(1999, 1, 1), price=200, fee=3):
    buy(SavingTypeFactory(title=title, fee_source=fee_source), price, fee, when=day)


TODAY = date(1999, 1, 1)
FORECAST_TODAY = date(1999, 1, 15)
NO_INCOMES_TODAY = date(1999, 6, 1)
JAN_1, FEB_1, MAY_10 = date(1999, 1, 1), date(1999, 2, 1), date(1999, 5, 10)


def _month_balance(user):
    user.month = 1
    return [month_load_service(user, TODAY)["info"]["fact"]["balance"]]


def _forecast_end_balance(user):
    return [forecast_load_service(user, FORECAST_TODAY)["data"][1]]


def _no_incomes_spend(user):
    user.journal.unnecessary_savings = True
    user.journal.save()
    actual = no_incomes_load_service(user, 1999, NO_INCOMES_TODAY, months=1)
    return [actual["avg_expenses"], actual["save_sum"]]


@pytest.mark.parametrize(
    "read, fee_source, day, price, figures",
    [
        (_month_balance, ACCOUNT, JAN_1, 200, [797]),
        (_month_balance, INVESTMENT, JAN_1, 200, [800]),
        (_month_balance, ACCOUNT, FEB_1, 200, [1000]),
        (_forecast_end_balance, ACCOUNT, JAN_1, 200, [797]),
        (_forecast_end_balance, INVESTMENT, JAN_1, 200, [800]),
        (_forecast_end_balance, ACCOUNT, JAN_1, 0, [997]),
        (_no_incomes_spend, ACCOUNT, MAY_10, 200, [203, 203]),
        (_no_incomes_spend, INVESTMENT, MAY_10, 200, [200, 200]),
    ],
    ids=[
        "month-account",
        "month-investment",
        "month-another_month",
        "forecast-account",
        "forecast-investment",
        "forecast-fee_with_no_price",
        "no_incomes-account",
        "no_incomes-investment",
    ],
)
def test_a_fee_counts_only_when_the_account_is_charged(
    main_user, read, fee_source, day, price, figures
):
    with quiet_build(main_user):
        IncomeFactory(price=1000)
        _purchase(fee_source, day=day, price=price)

    assert read(main_user) == figures


def test_month_savings_stay_the_purchase_price(main_user):
    main_user.month = 1
    with quiet_build(main_user):
        IncomeFactory(price=1000)
        _purchase(ACCOUNT)

    actual = month_load_service(main_user, TODAY)

    assert actual["info"]["fact"]["saving"] == 200
    assert actual["month_table"]["total_row"]["savings"] == 200


@pytest.mark.parametrize(
    "load, day, user_month, unnecessary_savings",
    [
        pytest.param(
            lambda user: month_load_service(user, TODAY), TODAY, 1, False, id="month"
        ),
        pytest.param(
            lambda user: forecast_load_service(user, FORECAST_TODAY),
            TODAY,
            12,
            False,
            id="forecast",
        ),
        pytest.param(
            lambda user: no_incomes_load_service(user, 1999, NO_INCOMES_TODAY),
            date(1999, 5, 10),
            12,
            True,
            id="no_incomes",
        ),
    ],
)
def test_query_count_does_not_grow(
    main_user, load, day, user_month, unnecessary_savings
):
    main_user.month = user_month
    main_user.journal.unnecessary_savings = unnecessary_savings
    main_user.journal.save()

    with quiet_build(main_user):
        for i in range(2):
            _purchase(ACCOUNT, title=f"T{i}", day=day)
    two = count_queries(lambda: load(main_user))

    with quiet_build(main_user):
        for i in range(2, 6):
            _purchase(ACCOUNT, title=f"T{i}", day=day)

    assert count_queries(lambda: load(main_user)) == two
