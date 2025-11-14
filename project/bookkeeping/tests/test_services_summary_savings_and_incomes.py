from types import SimpleNamespace

import pytest
from mock import patch

from ..services.summary_savings_and_incomes import Service


@pytest.fixture(name="incomes")
def fixture_incomes():
    return [
        {"year": 1, "sum": 10},
        {"year": 2, "sum": 11},
        {"year": 3, "sum": 12},
    ]


@pytest.fixture(name="savings")
def fixture_savings():
    return [
        {"year": 1, "sum": 20},
        {"year": 2, "sum": 21},
        {"year": 3, "sum": 22},
    ]


@patch(
    "project.bookkeeping.services.summary_savings_and_incomes.years",
    return_value=[1, 2, 3],
)
def test_chart_data_categories(mck, main_user):
    actual = Service(main_user, SimpleNamespace(incomes=[], savings=[])).chart_data()

    assert actual["categories"] == [1, 2]


@patch(
    "project.bookkeeping.services.summary_savings_and_incomes.years",
    return_value=[1, 2, 3, 4],
)
def test_chart_data_incomes(mck, incomes, main_user):
    actual = Service(
        main_user, SimpleNamespace(incomes=incomes, savings=[])
    ).chart_data()

    assert actual["incomes"] == [10, 11, 12]


@patch(
    "project.bookkeeping.services.summary_savings_and_incomes.years",
    return_value=[1, 2, 3, 4],
)
def test_chart_data_incomes_no_record(mck, incomes, main_user):
    del incomes[1]

    actual = Service(
        main_user, SimpleNamespace(incomes=incomes, savings=[])
    ).chart_data()

    assert actual["incomes"] == [10, 0, 12]


@patch(
    "project.bookkeeping.services.summary_savings_and_incomes.years",
    return_value=[1, 2, 3, 4],
)
def test_chart_data_savings(mck, incomes, savings, main_user):
    actual = Service(
        main_user, SimpleNamespace(incomes=incomes, savings=savings)
    ).chart_data()

    assert actual["savings"] == [20, 21, 22]


@patch(
    "project.bookkeeping.services.summary_savings_and_incomes.years",
    return_value=[1, 2, 3, 4],
)
def test_chart_data_savings_no_record(mck, incomes, savings, main_user):
    del savings[1]

    actual = Service(
        main_user, SimpleNamespace(incomes=incomes, savings=savings)
    ).chart_data()

    assert actual["savings"] == [20, 0, 22]


@patch(
    "project.bookkeeping.services.summary_savings_and_incomes.years",
    return_value=[1, 2, 3, 4],
)
def test_chart_data_percents(mck, incomes, savings, main_user):
    actual = Service(
        main_user, SimpleNamespace(incomes=incomes, savings=savings)
    ).chart_data()

    assert actual["percents"] == pytest.approx([200, 190.91, 183.33], 0.01)


@patch(
    "project.bookkeeping.services.summary_savings_and_incomes.years",
    return_value=[1, 2, 3, 4],
)
def test_chart_data_percents_no_record(mck, incomes, savings, main_user):
    del incomes[1]
    del savings[2]

    actual = Service(
        main_user, SimpleNamespace(incomes=incomes, savings=savings)
    ).chart_data()

    assert actual["percents"] == [200, 0, 0]
