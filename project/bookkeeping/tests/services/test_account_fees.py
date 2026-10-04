from datetime import date

import pytest
import time_machine
from django.db import connection
from django.test.utils import CaptureQueriesContext

from ....incomes.tests.factories import IncomeFactory
from ....savings.models import SavingType
from ....savings.tests.factories import SavingFactory, SavingTypeFactory
from ...lib.no_incomes import load_service as no_incomes_load_service
from ...services.forecast.presenters import load_service as forecast_load_service
from ...services.month.presenters import load_service as month_load_service

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


def _queries(func, *args):
    with CaptureQueriesContext(connection) as ctx:
        func(*args)
    return len(ctx)


# Month view
@pytest.mark.parametrize("fee_source, balance", [(ACCOUNT, 797), (INVESTMENT, 800)])
def test_month_balance_subtracts_account_fees_only(main_user, fee_source, balance):
    main_user.month = 1
    IncomeFactory(price=1000)
    _purchase(fee_source)

    actual = month_load_service(main_user)

    assert actual["info"]["fact"]["balance"] == balance


def test_month_savings_stay_the_purchase_price(main_user):
    main_user.month = 1
    IncomeFactory(price=1000)
    _purchase(ACCOUNT)

    actual = month_load_service(main_user)

    assert actual["info"]["fact"]["saving"] == 200
    assert actual["month_table"]["total_row"]["savings"] == 200


def test_month_account_fee_of_another_month_is_left_out(main_user):
    main_user.month = 1
    IncomeFactory(price=1000)
    _purchase(ACCOUNT, day=date(1999, 2, 1))

    actual = month_load_service(main_user)

    assert actual["info"]["fact"]["balance"] == 1000


def test_month_query_count_does_not_grow(main_user):
    main_user.month = 1
    for i in range(2):
        _purchase(ACCOUNT, title=f"T{i}")
    two = _queries(month_load_service, main_user)

    for i in range(2, 6):
        _purchase(ACCOUNT, title=f"T{i}")

    assert _queries(month_load_service, main_user) == two


# Forecast
@time_machine.travel("1999-01-15")
@pytest.mark.parametrize("fee_source, end", [(ACCOUNT, 797), (INVESTMENT, 800)])
def test_forecast_end_balance_subtracts_account_fees_only(main_user, fee_source, end):
    IncomeFactory(price=1000)
    _purchase(fee_source)

    actual = forecast_load_service(main_user)

    assert actual["data"][1] == end


@time_machine.travel("1999-01-15")
def test_forecast_counts_a_fee_paid_with_no_price(main_user):
    IncomeFactory(price=1000)
    _purchase(ACCOUNT, price=None)

    actual = forecast_load_service(main_user)

    assert actual["data"][1] == 997


@time_machine.travel("1999-01-15")
def test_forecast_query_count_does_not_grow(main_user):
    for i in range(2):
        _purchase(ACCOUNT, title=f"T{i}")
    two = _queries(forecast_load_service, main_user)

    for i in range(2, 6):
        _purchase(ACCOUNT, title=f"T{i}")

    assert _queries(forecast_load_service, main_user) == two


# No incomes
@pytest.fixture(name="savings_are_spending")
def fixture_savings_are_spending(main_user):
    main_user.journal.unnecessary_savings = True
    main_user.journal.save()


@time_machine.travel("1999-06-01")
@pytest.mark.parametrize("fee_source, spent", [(ACCOUNT, 203), (INVESTMENT, 200)])
def test_no_incomes_spend_counts_account_fees_only(
    main_user, savings_are_spending, fee_source, spent
):
    _purchase(fee_source, day=date(1999, 5, 10))

    actual = no_incomes_load_service(main_user, 1999, months=1)

    assert actual["avg_expenses"] == spent
    assert actual["save_sum"] == spent


@time_machine.travel("1999-06-01")
def test_no_incomes_query_count_does_not_grow(main_user, savings_are_spending):
    for i in range(2):
        _purchase(ACCOUNT, title=f"T{i}", day=date(1999, 5, 10))
    two = _queries(no_incomes_load_service, main_user, 1999)

    for i in range(2, 6):
        _purchase(ACCOUNT, title=f"T{i}", day=date(1999, 5, 10))

    assert _queries(no_incomes_load_service, main_user, 1999) == two
