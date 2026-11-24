from datetime import date
from unittest.mock import MagicMock

import pytest

from ....accounts.tests.factories import AccountBalanceFactory, AccountFactory
from ....debts.models import Debt
from ....debts.tests.factories import (
    BorrowFactory,
    BorrowReturnFactory,
    LendFactory,
    LendReturnFactory,
)
from ....expenses.tests.factories import ExpenseFactory
from ....incomes.tests.factories import IncomeFactory
from ...services.index.presenters import (
    DebtsTable,
    IndexContextBuilder,
    MonthCharts,
)
from ...services.index.providers import IndexDataProvider


@pytest.mark.parametrize(
    "end, data",
    [
        pytest.param(70, [5, 70, 65], id="gain"),
        pytest.param(-20, [5, -20, -25], id="loss"),
    ],
)
def test_balance_short_context_data(end, data):
    obj = IndexContextBuilder(
        balance=MagicMock(amount_start=5, amount_end=end, year=2021)
    )
    actual = obj.balance_short_context()

    assert actual["title"] == ["2021 pradžioje", "2021 pabaigoje", "Balansas"]
    assert actual["data"] == data
    assert actual["highlight"] == [False, False, True]


GAP = [None] * 8
MONTH_NAMES = [
    "Sausis",
    "Vasaris",
    "Kovas",
    "Balandis",
    "Gegužė",
    "Birželis",
    "Liepa",
    "Rugpjūtis",
    "Rugsėjis",
    "Spalis",
    "Lapkritis",
    "Gruodis",
]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "today, months",
    [
        pytest.param(
            date(2000, 1, 1),
            {
                "incomes": [120] + [0] * 11,
                "incomes_average": 10,
                "expenses": [0, 24] + [0] * 9 + [36],
                "expenses_average": 5,
                "current_month": [False] * 12,
            },
            id="past_year_every_month_and_none_current",
        ),
        pytest.param(
            date(1999, 3, 31),
            {
                "incomes": [120, 0, 0, *GAP, 0],
                "incomes_average": 40,
                "expenses": [0, 24, 0, *GAP, 36],
                "expenses_average": 8,
                "current_month": [False, False, True] + [False] * 9,
            },
            id="this_year_to_march_and_december_holding_rows",
        ),
        pytest.param(
            date(1998, 6, 1),
            {
                "incomes": [120, 0, None, *GAP, 0],
                "incomes_average": 0,
                "expenses": [0, 24, None, *GAP, 36],
                "expenses_average": 0,
                "current_month": [False] * 12,
            },
            id="coming_year_only_months_holding_rows",
        ),
    ],
)
def test_month_charts_read_the_months_reached(main_user, today, months):
    IncomeFactory(date=date(1999, 1, 1), price=120)
    ExpenseFactory(date=date(1999, 2, 1), price=24)
    ExpenseFactory(date=date(1999, 12, 1), price=36)
    IncomeFactory(date=date(2000, 1, 1), price=70)

    actual = MonthCharts.load(main_user, today).context()

    assert actual == {
        "categories": MONTH_NAMES,
        "incomes_title": "Pajamos",
        "expenses_title": "Išlaidos",
        "balance_title": "Balansas",
        "average_title": "Vidurkis",
        "so_far": "iki šiol",
        **months,
    }


LEND, BORROW = Debt.DebtType.LEND, Debt.DebtType.BORROW
NO_DEBT = {"debt": 0, "debt_return": 0}


def _row(title, debt, debt_return, remaining):
    return {
        "title": title,
        "debt": debt,
        "debt_return": debt_return,
        "remaining": remaining,
    }


@pytest.mark.parametrize(
    "debts, rows",
    [
        pytest.param(
            {
                BORROW: {"debt": 99, "debt_return": 66},
                LEND: {"debt": 9, "debt_return": 3},
            },
            [_row("Paskolinta", 9, 3, 6), _row("Pasiskolinta", 99, 66, 33)],
            id="lend_before_borrow",
        ),
        pytest.param(
            {LEND: {"debt": 300, "debt_return": 300}, BORROW: NO_DEBT},
            [_row("Paskolinta", 300, 300, 0)],
            id="fully_repaid_lend_only",
        ),
        pytest.param(
            {LEND: NO_DEBT, BORROW: {"debt": 300, "debt_return": 300}},
            [_row("Pasiskolinta", 300, 300, 0)],
            id="fully_repaid_borrow_only",
        ),
        pytest.param({LEND: NO_DEBT, BORROW: NO_DEBT}, [], id="none"),
    ],
)
def test_debts_context_is_a_row_per_kind_with_a_debt(debts, rows):
    assert DebtsTable(debts=debts).debts_context() == rows


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
def test_debts_table_sums_each_kind_of_open_debt(main_user):
    LendReturnFactory(debt=LendFactory(price=100), price=50)
    BorrowFactory(price=200)
    BorrowFactory(price=999, closed=True)

    actual = DebtsTable.load(main_user).debts

    assert actual == {
        LEND: {"debt": 100, "debt_return": 50},
        BORROW: {"debt": 200, "debt_return": 0},
    }


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
    return mock


@pytest.mark.parametrize(
    "accounts_balance, state",
    [
        pytest.param(1600, "", id="equal"),
        pytest.param(1599, "mismatch", id="differ"),
    ],
)
def test_balance_context_checks_the_year_end_cash_flow_against_the_accounts(
    mock_year_balance, accounts_balance, state
):
    builder = IndexContextBuilder(balance=mock_year_balance)
    actual = builder.balance_context(accounts_balance=accounts_balance)

    assert actual == {
        "data": [100, 200, 300],
        "total_row": 600,
        "amount_end": 1600,
        "avg_row": 200,
        "cash_flow_check": state,
    }
