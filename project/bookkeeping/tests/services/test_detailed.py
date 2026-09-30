from datetime import date
from types import SimpleNamespace

import pytest
from mock import MagicMock

from ....expenses.tests.factories import (
    ExpenseFactory,
    ExpenseNameFactory,
    ExpenseTypeFactory,
)
from ....incomes.tests.factories import IncomeFactory
from ....savings.tests.factories import SavingFactory
from ...services.detailed.builders import DetailedTableBuilder
from ...services.detailed.dtos import DetailedDto
from ...services.detailed.presenters import build_context, load_service


@pytest.fixture(name="data")
def fixture_data():
    return SimpleNamespace(
        data=[
            {"date": date(1999, 1, 1), "sum": 4, "title": "Y"},
            {"date": date(1999, 2, 1), "sum": 8, "title": "Y"},
            {"date": date(1999, 1, 1), "sum": 1, "title": "X"},
            {"date": date(1999, 2, 1), "sum": 2, "title": "X"},
        ]
    )


def test_table_property(data):
    actual = DetailedTableBuilder(data, 1999).table

    assert len(actual[0]) == 14
    assert len(actual[1]) == 14

    assert actual[0]["title"] == "X"
    assert actual[0]["1"] == 1
    assert actual[0]["2"] == 2
    assert actual[0]["3"] == 0
    assert actual[0]["12"] == 0
    assert actual[0]["total_col"] == 3

    assert actual[1]["title"] == "Y"
    assert actual[1]["1"] == 4
    assert actual[1]["2"] == 8
    assert actual[1]["3"] == 0
    assert actual[1]["12"] == 0
    assert actual[1]["total_col"] == 12


def test_table_property_with_february_only(data):
    data = SimpleNamespace(
        data=[
            {"date": date(1999, 2, 1), "sum": 2, "title": "X"},
        ]
    )
    actual = DetailedTableBuilder(data, 1999).table

    assert len(actual[0]) == 14

    assert actual[0]["title"] == "X"
    assert actual[0]["1"] == 0
    assert actual[0]["2"] == 2
    assert actual[0]["3"] == 0
    assert actual[0]["12"] == 0
    assert actual[0]["total_col"] == 2


def test_table_property_no_data():
    data = SimpleNamespace(data=[])
    actual = DetailedTableBuilder(data, 1999).table

    assert actual == []


def test_total_row_property(data):

    actual = DetailedTableBuilder(data, 1999).total_row

    assert actual["1"] == 5
    assert actual["2"] == 10
    assert actual["3"] == 0
    assert actual["12"] == 0
    assert actual["total_col"] == 15


def test_total_row_property_no_data():
    data = SimpleNamespace(data=[])
    actual = DetailedTableBuilder(data, 1999).total_row

    assert actual == {}


# -------------------------------------------------------------------------------------
#                                                                             Fixtures
# -------------------------------------------------------------------------------------


@pytest.fixture
def dummy_sort_dto():
    """
    Creates a specific dataset to test sorting logic.
    Alpha:   Month 1 = 10,  Month 2 = 50.  Total = 60
    Bravo:   Month 1 = 100, Month 2 = 0.   Total = 100
    Charlie: Month 1 = 30,  Month 2 = 40.  Total = 70
    """
    return DetailedDto(
        data=[
            {"title": "Alpha", "date": date(2026, 1, 15), "sum": 10},
            {"title": "Alpha", "date": date(2026, 2, 15), "sum": 50},
            {"title": "Bravo", "date": date(2026, 1, 15), "sum": 100},
            {"title": "Bravo", "date": date(2026, 2, 15), "sum": 0},
            {"title": "Charlie", "date": date(2026, 1, 15), "sum": 30},
            {"title": "Charlie", "date": date(2026, 2, 15), "sum": 40},
        ]
    )


# -------------------------------------------------------------------------------------
#                                                                        Sorting Tests
# -------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "order, expected_titles, expected_active",
    [
        ("title", ["Alpha", "Bravo", "Charlie"], "title"),
        ("1", ["Bravo", "Charlie", "Alpha"], "1"),
        ("2", ["Alpha", "Charlie", "Bravo"], "2"),
        ("total_col", ["Bravo", "Charlie", "Alpha"], "total_col"),
        ("", ["Bravo", "Charlie", "Alpha"], "total_col"),
        ("nonsense", ["Bravo", "Charlie", "Alpha"], "total_col"),
        ("-1", ["Bravo", "Charlie", "Alpha"], "total_col"),
    ],
)
def test_load_service_sorts_by_order(
    mocker, dummy_sort_dto, order, expected_titles, expected_active
):
    mock_provider = mocker.patch(
        "project.bookkeeping.services.detailed.presenters.DetailedDataProvider"
    )
    mock_provider.return_value.get_incomes.return_value = dummy_sort_dto

    (table,) = load_service(MagicMock(year=2026), "income", order)

    assert [row["title"] for row in table["data"]] == expected_titles
    assert table["order"] == expected_active


# -------------------------------------------------------------------------------------
#                                                     build_context Tests
# -------------------------------------------------------------------------------------
def test_build_context_empty_data():
    mock_dto = MagicMock(data=[])

    result = build_context(
        title="Test Title", url_title="test-title", dto=mock_dto, year=2026, order=""
    )

    assert result == {}


# -------------------------------------------------------------------------------------
#                                                                 load_service Tests
# -------------------------------------------------------------------------------------
def test_load_service_income_category(mocker):
    user = MagicMock(year=2026)

    mock_dto = MagicMock(data=[{"sum": 100}])
    mock_provider = mocker.patch(
        "project.bookkeeping.services.detailed.presenters.DetailedDataProvider"
    )
    mock_provider.return_value.get_incomes.return_value = mock_dto

    mock_build = mocker.patch(
        "project.bookkeeping.services.detailed.presenters.build_context"
    )
    mock_build.return_value = {"mock": "context", "total": {"total_col": 0}}

    result = load_service(user, category="income")

    assert result == [mock_build.return_value]
    mock_provider.return_value.get_incomes.assert_called_once()


def test_load_service_saving_category(mocker):
    user = MagicMock(year=2026)

    mock_dto = MagicMock(data=[{"sum": 500}])
    mock_provider = mocker.patch(
        "project.bookkeeping.services.detailed.presenters.DetailedDataProvider"
    )
    mock_provider.return_value.get_savings.return_value = mock_dto

    mock_build = mocker.patch(
        "project.bookkeeping.services.detailed.presenters.build_context"
    )
    mock_build.return_value = {"mock": "context", "total": {"total_col": 0}}

    result = load_service(user, category="saving")

    assert result == [mock_build.return_value]
    mock_provider.return_value.get_savings.assert_called_once()


def test_load_service_unknown_category_not_found(mocker):
    user = MagicMock(year=2026)

    mock_provider = mocker.patch(
        "project.bookkeeping.services.detailed.presenters.DetailedDataProvider"
    )
    mock_provider.return_value.get_expense_type.return_value = None

    result = load_service(user, category="non_existent_slug")

    assert result == []


def _expense(type_title, name_title, **fields):
    expense_type = ExpenseTypeFactory(title=type_title)
    ExpenseFactory(
        expense_type=expense_type,
        expense_name=ExpenseNameFactory(title=name_title, parent=expense_type),
        **fields,
    )


def _titles(user):
    return [context["title"] for context in load_service(user, "expenses")]


@pytest.mark.django_db
def test_load_service_expense_types_by_type_title(main_user):
    _expense("Zeta", "Alpha")
    _expense("Beta", "Omega")

    assert _titles(main_user) == ["Beta", "Zeta"]


@pytest.mark.django_db
def test_load_service_expense_types_in_code_point_order(main_user):
    _expense("Šildymas", "Alpha")
    _expense("Zeta", "Omega")

    assert _titles(main_user) == ["Zeta", "Šildymas"]


@pytest.mark.django_db
def test_load_service_expense_types_by_total_biggest_first(main_user):
    _expense("A", "Alpha", price=10000)
    _expense("B", "Omega", price=30000)

    assert _titles(main_user) == ["B", "A"]


@pytest.mark.django_db
def test_load_service_expense_rows_by_total_below_a_bigger_type(main_user):
    expense_type = ExpenseTypeFactory(title="A")
    for title, price in (("Beta", 10000), ("Alpha", 5000)):
        ExpenseFactory(
            price=price,
            expense_type=expense_type,
            expense_name=ExpenseNameFactory(title=title, parent=expense_type),
        )
    _expense("B", "Omega", price=30000)

    _, table = load_service(main_user, "expenses")

    assert [row["title"] for row in table["data"]] == ["Beta", "Alpha"]


@pytest.mark.django_db
def test_load_service_expense_rows_of_equal_total_keep_title_order(main_user):
    expense_type = ExpenseTypeFactory(title="A")
    for title in ("Zulu", "Alpha"):
        ExpenseFactory(
            price=5000,
            expense_type=expense_type,
            expense_name=ExpenseNameFactory(title=title, parent=expense_type),
        )

    (table,) = load_service(main_user, "expenses")

    assert [row["title"] for row in table["data"]] == ["Alpha", "Zulu"]


@pytest.mark.django_db
def test_load_service_expenses_are_the_types_alone(main_user):
    _expense("Beta", "Alpha")
    IncomeFactory()
    SavingFactory()

    assert _titles(main_user) == ["Beta"]


@pytest.mark.django_db
def test_load_service_expenses_skip_a_type_without_rows(main_user):
    _expense("Beta", "Alpha")
    ExpenseTypeFactory(title="Empty")

    assert _titles(main_user) == ["Beta"]


@pytest.mark.django_db
def test_load_service_expense_type_carries_its_url_and_table_id(main_user):
    _expense("Zeta Type", "Alpha")

    (table,) = load_service(main_user, "expenses")

    assert table["url"] == "/detailed/expenses/zeta-type/"
    assert table["table_id"] == "detailed-zeta-type-table"
    assert "target" not in table


@pytest.mark.django_db
def test_load_service_type_slug_reads_its_own_type(main_user):
    _expense("Income", "Alpha")
    IncomeFactory()

    (table,) = load_service(main_user, "expenses", type_slug="income")

    assert table["title"] == "Income"
    assert [row["title"] for row in table["data"]] == ["Alpha"]


@pytest.mark.django_db
def test_load_service_type_slug_reads_that_type_only(main_user):
    _expense("Beta", "Alpha")
    _expense("Zeta", "Omega")

    (table,) = load_service(main_user, "expenses", type_slug="zeta")

    assert table["title"] == "Zeta"


@pytest.mark.django_db
def test_load_service_unknown_type_slug_is_empty(main_user):
    _expense("Beta", "Alpha")

    assert load_service(main_user, "expenses", type_slug="nonsense") == []
