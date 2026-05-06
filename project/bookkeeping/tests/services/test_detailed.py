from datetime import date
from types import SimpleNamespace

import pytest
from mock import MagicMock

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
    "order_param, expected_first, expected_last",
    [
        # 1. Sort by Title
        ("title", "Alpha", "Charlie"),  # A, B, C
        ("-title", "Charlie", "Alpha"),  # C, B, A
        # 2. Sort by Total Column
        ("total_col", "Alpha", "Bravo"),  # 60, 70, 100
        ("-total_col", "Bravo", "Alpha"),  # 100, 70, 60
        # 3. Sort by Month 1 (January)
        ("1", "Alpha", "Bravo"),  # 10, 30, 100
        ("-1", "Bravo", "Alpha"),  # 100, 30, 10
        # 4. Sort by Month 2 (February)
        ("2", "Bravo", "Alpha"),  # 0, 40, 50
        ("-2", "Alpha", "Bravo"),  # 50, 40, 0
        # 5. Invalid sort column (should silently ignore and preserve default order)
        ("invalid_column", "Alpha", "Charlie"),
        ("-invalid_col", "Alpha", "Charlie"),
        ("", "Alpha", "Charlie"),  # Empty string
    ],
)
def test_detailed_table_builder_sorting(
    dummy_sort_dto, order_param, expected_first, expected_last
):
    """Proves the Polars DataFrame sorts dynamically based on the order string."""
    builder = DetailedTableBuilder(dto=dummy_sort_dto, year=2026, order=order_param)

    table = builder.table

    # We only need to check the first and last elements to prove the sort worked
    assert table[0]["title"] == expected_first
    assert table[-1]["title"] == expected_last


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
    mock_build.return_value = {"mock": "context"}

    result = load_service(user, category="income")

    assert result == [{"mock": "context"}]
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
    mock_build.return_value = {"mock": "context"}

    result = load_service(user, category="saving")

    assert result == [{"mock": "context"}]
    mock_provider.return_value.get_savings.assert_called_once()


def test_load_service_unknown_category_not_found(mocker):
    user = MagicMock(year=2026)

    mock_provider = mocker.patch(
        "project.bookkeeping.services.detailed.presenters.DetailedDataProvider"
    )
    mock_provider.return_value.get_expense_type.return_value = None

    result = load_service(user, category="non_existent_slug")

    assert result == []
