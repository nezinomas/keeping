from datetime import date
from unittest.mock import MagicMock

import pytest

from ....accounts.tests.factories import AccountBalanceFactory, AccountFactory
from ....core.lib.translation import month_names
from ....debts.models import Debt
from ....debts.tests.factories import (
    BorrowFactory,
    BorrowReturnFactory,
    LendFactory,
    LendReturnFactory,
)
from ...services.index.presenters import IndexContextBuilder
from ...services.index.providers import IndexDataProvider

MODULE_PATH = "project.bookkeeping.services.index"


@pytest.mark.parametrize(
    "end, data",
    [
        pytest.param(70, [5, 70, 65], id="gain"),
        pytest.param(-20, [5, -20, -25], id="loss"),
    ],
)
def test_balance_short_context_data(end, data):
    obj = IndexContextBuilder(
        balance=MagicMock(amount_start=5, amount_end=end, year=2021), debts={}
    )
    actual = obj.balance_short_context()

    assert actual["title"] == ["2021 pradžioje", "2021 pabaigoje", "Balansas"]
    assert actual["data"] == data
    assert actual["highlight"] == [False, False, True]


def test_chart_balance_context(mock_year_balance):
    obj = IndexContextBuilder(balance=mock_year_balance, debts={})
    actual = obj.chart_balance_context()

    assert actual["categories"] == list(month_names().values())
    assert actual["incomes"] == [50, 50, 50]
    assert actual["incomes_title"] == "Pajamos"
    assert actual["expenses"] == [10, 10, 10]
    assert actual["expenses_title"] == "Išlaidos"


@pytest.mark.parametrize(
    "kind, context",
    [
        pytest.param(
            Debt.DebtType.BORROW, IndexContextBuilder.borrow_context, id="borrow"
        ),
        pytest.param(Debt.DebtType.LEND, IndexContextBuilder.lend_context, id="lend"),
    ],
)
def test_debt_context_without_debt_is_empty(kind, context):
    obj = IndexContextBuilder(
        balance=MagicMock(), debts={kind: {"debt": 0, "debt_return": 0}}
    )

    assert context(obj) == {}


@pytest.mark.parametrize(
    "kind, context, titles, debt, debt_return",
    [
        pytest.param(
            Debt.DebtType.BORROW,
            IndexContextBuilder.borrow_context,
            ("Pasiskolinta", "Grąžinau"),
            99,
            66,
            id="borrow_part_returned",
        ),
        pytest.param(
            Debt.DebtType.BORROW,
            IndexContextBuilder.borrow_context,
            ("Pasiskolinta", "Grąžinau"),
            300,
            300,
            id="borrow_fully_repaid",
        ),
        pytest.param(
            Debt.DebtType.LEND,
            IndexContextBuilder.lend_context,
            ("Paskolinta", "Grąžino"),
            9,
            3,
            id="lend_part_returned",
        ),
        pytest.param(
            Debt.DebtType.LEND,
            IndexContextBuilder.lend_context,
            ("Paskolinta", "Grąžino"),
            300,
            300,
            id="lend_fully_repaid",
        ),
    ],
)
def test_debt_context(kind, context, titles, debt, debt_return):
    obj = IndexContextBuilder(
        balance=MagicMock(),
        debts={kind: {"debt": debt, "debt_return": debt_return}},
    )
    actual = context(obj)

    assert actual["title"] == list(titles)
    assert actual["data"] == [debt, debt_return]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "past_by_year, expect",
    [
        pytest.param({2026: [3000, 2000], 2025: [700]}, 5000, id="a_sum"),
        pytest.param({2025: [700]}, 0, id="no_sum"),
    ],
)
def test_index_data_provider_amount_start(main_user, past_by_year, expect):
    main_user.year = 2026
    # every account is saved before any balance row: an account's save re-syncs
    accounts = {
        (year, past): AccountFactory(title=f"{year}-{past}")
        for year, pasts in past_by_year.items()
        for past in pasts
    }
    for year, pasts in past_by_year.items():
        for past in pasts:
            AccountBalanceFactory(
                account=accounts[year, past],
                year=year,
                past=past,
                balance=past + 111,
            )

    actual = IndexDataProvider(main_user).get_data().amount_start

    assert actual == expect


@pytest.mark.django_db
def test_index_data_provider_get_debts(mocker, main_user):
    sums = {
        Debt.DebtType.LEND: {"debt": 100, "debt_return": 50},
        Debt.DebtType.BORROW: {"debt": 200, "debt_return": 0},
    }
    mocker.patch(
        f"{MODULE_PATH}.providers.DebtModelService",
        side_effect=lambda user, kind: MagicMock(sum_all=lambda: sums[kind]),
    )

    actual = IndexDataProvider(main_user).get_data().debts

    assert actual[Debt.DebtType.LEND] == {"debt": 100, "debt_return": 50}
    assert actual[Debt.DebtType.BORROW] == {"debt": 200, "debt_return": 0}


@pytest.mark.django_db
def test_index_data_provider_monthly_debts(main_user):
    day = date(main_user.year, 3, 5)
    journal = main_user.journal
    lend = LendFactory(journal=journal, date=day, price=100)
    borrow = BorrowFactory(journal=journal, date=day, price=200)
    LendReturnFactory(debt=lend, date=day, price=10)
    BorrowReturnFactory(debt=borrow, date=day, price=30)

    monthly = IndexDataProvider(main_user).get_data().monthly_data
    actual = sorted(
        (row for row in monthly if row["title"].startswith(("lend", "borrow"))),
        key=lambda row: row["title"],
    )

    month = date(main_user.year, 3, 1)
    assert actual == [
        {"date": month, "title": "borrow", "sum": 200},
        {"date": month, "title": "borrow_return", "sum": 30},
        {"date": month, "title": "lend", "sum": 100},
        {"date": month, "title": "lend_return", "sum": 10},
    ]


@pytest.fixture
def mock_year_balance(mocker):
    mock = mocker.Mock()
    mock.balance = [100, 200, 300]
    mock.total_row = 600
    mock.amount_start = 1000
    mock.amount_end = 1600
    mock.average = 200
    mock.year = 2026
    mock.income_data = [50, 50, 50]
    mock.expense_data = [10, 10, 10]
    mock.avg_incomes = 50
    mock.avg_expenses = 10
    return mock


def test_index_context_builder_balance_context(mock_year_balance):
    builder = IndexContextBuilder(balance=mock_year_balance, debts={})
    actual = builder.balance_context()

    assert actual["data"] == [100, 200, 300]
    assert actual["total_row"] == 600
    assert actual["amount_end"] == 1600
    assert actual["avg_row"] == 200


def test_index_context_builder_averages_context(mock_year_balance):
    builder = IndexContextBuilder(balance=mock_year_balance, debts={})
    actual = builder.averages_context()

    assert actual["data"] == [50, 10]
    assert actual["title"] == ["Vidutinės pajamos", "Vidutinės išlaidos"]
