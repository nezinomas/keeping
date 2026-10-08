import pytest
from mock import MagicMock

from ....core.lib.translation import month_names
from ...services.index.dtos import IndexDataDTO
from ...services.index.presenters import IndexContextBuilder
from ...services.index.providers import IndexDataProvider

MODULE_PATH = "project.bookkeeping.services.index"


def test_balance_short_context_data():
    obj = IndexContextBuilder(
        balance=MagicMock(amount_start=5, amount_end=70, year=2021)
    )
    actual = obj.balance_short_context()

    assert actual["title"] == ["2021 pradžioje", "2021 pabaigoje", "Balansas"]
    assert actual["data"] == [5, 70, 65]


def test_balance_short_highlighted():
    obj = IndexContextBuilder(balance=MagicMock(amount_start=5, amount_end=-20))
    actual = obj.balance_short_context()

    assert actual["data"] == [5, -20, -25]
    assert actual["highlight"] == [False, False, True]


def test_chart_balance_context(mock_year_balance):
    obj = IndexContextBuilder(balance=mock_year_balance)
    actual = obj.chart_balance_context()

    assert actual["categories"] == list(month_names().values())
    assert actual["incomes"] == [50, 50, 50]
    assert actual["incomes_title"] == "Pajamos"
    assert actual["expenses"] == [10, 10, 10]
    assert actual["expenses_title"] == "Išlaidos"


def test_borrow_context():
    obj = IndexContextBuilder(
        balance=MagicMock(), debts={"borrow": {"debt": 99, "debt_return": 66}}
    )
    actual = obj.borrow_context()

    assert "Pasiskolinta" in actual["title"]
    assert "Grąžinau" in actual["title"]
    assert actual["data"] == [99, 66]


@pytest.mark.parametrize(
    "kind, context",
    [
        pytest.param("borrow", IndexContextBuilder.borrow_context, id="borrow"),
        pytest.param("lend", IndexContextBuilder.lend_context, id="lend"),
    ],
)
@pytest.mark.parametrize(
    "debt",
    [
        pytest.param({"debt": None, "debt_return": None}, id="no_data"),
        pytest.param({"debt": 0, "debt_return": 0}, id="zero_debt"),
    ],
)
def test_debt_context_without_debt_is_empty(kind, context, debt):
    obj = IndexContextBuilder(balance=MagicMock(), debts={kind: debt})

    assert context(obj) == {}


def test_lend_context():
    obj = IndexContextBuilder(
        balance=MagicMock(), debts={"lend": {"debt": 9, "debt_return": 3}}
    )
    actual = obj.lend_context()

    assert "Paskolinta" in actual["title"]
    assert "Grąžino" in actual["title"]
    assert actual["data"] == [9, 3]


def test_index_data_dto():
    dto = IndexDataDTO(
        amount_start=1000,
        monthly_data=[{"month": 1, "sum": 500}],
        debts={"lend": {"debt": 100, "debt_return": 50}},
    )

    assert dto.amount_start == 1000
    assert len(dto.monthly_data) == 1
    assert dto.debts["lend"]["debt"] == 100


@pytest.mark.django_db
@pytest.mark.parametrize(
    "past_sum, expect",
    [
        pytest.param(5000, 5000, id="a_sum"),
        pytest.param(None, 0, id="no_sum"),
    ],
)
def test_index_data_provider_amount_start(mocker, main_user, past_sum, expect):
    main_user.year = 2026
    mock_balance_service = mocker.patch(
        f"{MODULE_PATH}.providers.AccountBalanceModelService"
    )
    mock_year = mock_balance_service.return_value.year.return_value
    mock_year.aggregate.return_value = {"past__sum": past_sum}

    actual = IndexDataProvider(main_user).get_data().amount_start

    assert actual == expect
    mock_balance_service.return_value.year.assert_called_once_with(2026)


@pytest.mark.django_db
def test_index_data_provider_get_debts(mocker, main_user):
    sums = {
        "lend": {"debt": 100, "debt_return": 50},
        "borrow": {"debt": 200, "debt_return": 0},
    }
    mocker.patch(
        f"{MODULE_PATH}.providers.DebtModelService",
        side_effect=lambda user, kind: MagicMock(sum_all=lambda: sums[kind]),
    )

    actual = IndexDataProvider(main_user).get_data().debts

    assert actual["lend"] == {"debt": 100, "debt_return": 50}
    assert actual["borrow"] == {"debt": 200, "debt_return": 0}


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
    builder = IndexContextBuilder(balance=mock_year_balance)
    actual = builder.balance_context()

    assert actual["data"] == [100, 200, 300]
    assert actual["total_row"] == 600
    assert actual["amount_end"] == 1600
    assert actual["avg_row"] == 200


def test_index_context_builder_averages_context(mock_year_balance):
    builder = IndexContextBuilder(balance=mock_year_balance)
    actual = builder.averages_context()

    assert actual["data"] == [50, 10]
    assert len(actual["title"]) == 2
