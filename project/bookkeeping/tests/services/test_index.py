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
from ....expenses.tests.factories import ExpenseFactory
from ....incomes.tests.factories import IncomeFactory
from ...services.index.presenters import (
    DebtsTable,
    IncomesExpensesChart,
    IndexContextBuilder,
    cash_flow_check,
)
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
        balance=MagicMock(amount_start=5, amount_end=end, year=2021)
    )
    actual = obj.balance_short_context()

    assert actual["title"] == ["2021 pradžioje", "2021 pabaigoje", "Balansas"]
    assert actual["data"] == data
    assert actual["highlight"] == [False, False, True]


@pytest.mark.django_db
def test_incomes_expenses_chart_reads_the_year_s_incomes_and_expenses_by_month(
    main_user,
):
    IncomeFactory(date=date(1999, 1, 1), price=50)
    ExpenseFactory(date=date(1999, 2, 1), price=10)
    IncomeFactory(date=date(2000, 1, 1), price=70)

    actual = IncomesExpensesChart.load(main_user).context()

    assert actual == {
        "categories": list(month_names().values()),
        "incomes": [50] + [0] * 11,
        "incomes_title": "Pajamos",
        "expenses": [0, 10] + [0] * 10,
        "expenses_title": "Išlaidos",
    }


@pytest.mark.parametrize(
    "kind, context",
    [
        pytest.param(Debt.DebtType.BORROW, DebtsTable.borrow_context, id="borrow"),
        pytest.param(Debt.DebtType.LEND, DebtsTable.lend_context, id="lend"),
    ],
)
def test_debt_context_without_debt_is_empty(kind, context):
    obj = DebtsTable(debts={kind: {"debt": 0, "debt_return": 0}})

    assert context(obj) == {}


@pytest.mark.parametrize(
    "kind, context, titles, debt, debt_return",
    [
        pytest.param(
            Debt.DebtType.BORROW,
            DebtsTable.borrow_context,
            ("Pasiskolinta", "Grąžinau"),
            99,
            66,
            id="borrow_part_returned",
        ),
        pytest.param(
            Debt.DebtType.BORROW,
            DebtsTable.borrow_context,
            ("Pasiskolinta", "Grąžinau"),
            300,
            300,
            id="borrow_fully_repaid",
        ),
        pytest.param(
            Debt.DebtType.LEND,
            DebtsTable.lend_context,
            ("Paskolinta", "Grąžino"),
            9,
            3,
            id="lend_part_returned",
        ),
        pytest.param(
            Debt.DebtType.LEND,
            DebtsTable.lend_context,
            ("Paskolinta", "Grąžino"),
            300,
            300,
            id="lend_fully_repaid",
        ),
    ],
)
def test_debt_context(kind, context, titles, debt, debt_return):
    obj = DebtsTable(debts={kind: {"debt": debt, "debt_return": debt_return}})
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
def test_debts_table_sums_each_kind(mocker, main_user):
    sums = {
        Debt.DebtType.LEND: {"debt": 100, "debt_return": 50},
        Debt.DebtType.BORROW: {"debt": 200, "debt_return": 0},
    }
    mocker.patch(
        f"{MODULE_PATH}.presenters.DebtModelService",
        side_effect=lambda user, kind: MagicMock(sum_all=lambda: sums[kind]),
    )

    actual = DebtsTable.load(main_user).debts

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
    return mock


def test_index_context_builder_balance_context(mock_year_balance):
    builder = IndexContextBuilder(balance=mock_year_balance)
    actual = builder.balance_context(accounts_balance=1500)

    assert actual == {
        "data": [100, 200, 300],
        "total_row": 600,
        "amount_end": 1600,
        "avg_row": 200,
        "cash_flow_check": "mismatch",
    }


@pytest.mark.parametrize(
    "cash_flow, accounts_balance, state",
    [
        pytest.param(100000, 100000, "", id="equal"),
        pytest.param(100000, 99999, "mismatch", id="differ"),
    ],
)
def test_cash_flow_check(cash_flow, accounts_balance, state):
    assert cash_flow_check(cash_flow, accounts_balance) == state
