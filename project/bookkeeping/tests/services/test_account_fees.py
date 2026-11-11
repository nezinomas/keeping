from datetime import date

import pytest

from ....core.tests.utils import count_queries
from ....incomes.tests.factories import IncomeFactory
from ....savings.models import SavingType
from ....savings.tests.factories import SavingFactory, SavingTypeFactory
from ...lib.no_incomes import load_service as no_incomes_load_service
from ...services.forecast.presenters import load_service as forecast_load_service
from ...services.month.presenters import load_service as month_load_service
from ..helper import quiet_build

pytestmark = pytest.mark.django_db

ACCOUNT = SavingType.FeeSource.ACCOUNT
INVESTMENT = SavingType.FeeSource.INVESTMENT


def _purchase(fee_source, title="Fund", day=date(1999, 1, 1), price=200, fee=3):
    SavingFactory(
        date=day,
        price=price,
        fee=fee,
        saving_type=SavingTypeFactory(title=title, fee_source=fee_source),
    )


TODAY = date(1999, 1, 1)
FORECAST_TODAY = date(1999, 1, 15)
NO_INCOMES_TODAY = date(1999, 6, 1)


@pytest.mark.parametrize(
    "fee_source, day, balance",
    [
        pytest.param(ACCOUNT, date(1999, 1, 1), 797, id="account"),
        pytest.param(INVESTMENT, date(1999, 1, 1), 800, id="investment"),
        pytest.param(ACCOUNT, date(1999, 2, 1), 1000, id="another_month"),
    ],
)
def test_month_balance_subtracts_account_fees_only(main_user, fee_source, day, balance):
    main_user.month = 1
    IncomeFactory(price=1000)
    _purchase(fee_source, day=day)

    actual = month_load_service(main_user, TODAY)

    assert actual["info"]["fact"]["balance"] == balance


def test_month_savings_stay_the_purchase_price(main_user):
    main_user.month = 1
    IncomeFactory(price=1000)
    _purchase(ACCOUNT)

    actual = month_load_service(main_user, TODAY)

    assert actual["info"]["fact"]["saving"] == 200
    assert actual["month_table"]["total_row"]["savings"] == 200


@pytest.mark.parametrize(
    "fee_source, price, end",
    [
        pytest.param(ACCOUNT, 200, 797, id="account"),
        pytest.param(INVESTMENT, 200, 800, id="investment"),
        pytest.param(ACCOUNT, 0, 997, id="fee_with_no_price"),
    ],
)
def test_forecast_end_balance_subtracts_account_fees_only(
    main_user, fee_source, price, end
):
    IncomeFactory(price=1000)
    _purchase(fee_source, price=price)

    actual = forecast_load_service(main_user, FORECAST_TODAY)

    assert actual["data"][1] == end


@pytest.fixture(name="savings_are_spending")
def fixture_savings_are_spending(main_user):
    main_user.journal.unnecessary_savings = True
    main_user.journal.save()


@pytest.mark.parametrize("fee_source, spent", [(ACCOUNT, 203), (INVESTMENT, 200)])
def test_no_incomes_spend_counts_account_fees_only(
    main_user, savings_are_spending, fee_source, spent
):
    _purchase(fee_source, day=date(1999, 5, 10))

    actual = no_incomes_load_service(main_user, 1999, NO_INCOMES_TODAY, months=1)

    assert actual["avg_expenses"] == spent
    assert actual["save_sum"] == spent


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
