from types import SimpleNamespace
from typing import cast

import pytest

from ..services.summary_savings_and_incomes import Data, Service

MODULE_PATH = "project.bookkeeping.services.summary_savings_and_incomes.years"


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


def test_chart_data_categories(mocker, main_user):
    mocker.patch(MODULE_PATH, return_value=[1, 2, 3])

    data = cast(Data, SimpleNamespace(incomes=[], savings=[]))
    actual = Service(main_user, data).chart_data()

    assert actual["categories"] == [1, 2]


def test_chart_data_incomes(mocker, incomes, main_user):
    mocker.patch(MODULE_PATH, return_value=[1, 2, 3, 4])

    data = cast(Data, SimpleNamespace(incomes=incomes, savings=[]))
    actual = Service(main_user, data).chart_data()

    assert actual["incomes"] == [10, 11, 12]


def test_chart_data_incomes_no_record(mocker, incomes, main_user):
    mocker.patch(MODULE_PATH, return_value=[1, 2, 3, 4])
    del incomes[1]

    data = cast(Data, SimpleNamespace(incomes=incomes, savings=[]))
    actual = Service(main_user, data).chart_data()

    assert actual["incomes"] == [10, 0, 12]


def test_chart_data_savings(mocker, incomes, savings, main_user):
    mocker.patch(MODULE_PATH, return_value=[1, 2, 3, 4])
    data = cast(Data, SimpleNamespace(incomes=incomes, savings=savings))
    actual = Service(main_user, data).chart_data()

    assert actual["savings"] == [20, 21, 22]


def test_chart_data_savings_no_record(mocker, incomes, savings, main_user):
    mocker.patch(MODULE_PATH, return_value=[1, 2, 3, 4])
    del savings[1]

    data = cast(Data, SimpleNamespace(incomes=incomes, savings=savings))
    actual = Service(main_user, data).chart_data()

    assert actual["savings"] == [20, 0, 22]


def test_chart_data_percents(mocker, incomes, savings, main_user):
    mocker.patch(MODULE_PATH, return_value=[1, 2, 3, 4])
    data = cast(Data, SimpleNamespace(incomes=incomes, savings=savings))
    actual = Service(main_user, data).chart_data()

    assert actual["percents"] == pytest.approx([200, 190.91, 183.33], 0.01)


def test_chart_data_percents_no_record(mocker, incomes, savings, main_user):
    mocker.patch(MODULE_PATH, return_value=[1, 2, 3, 4])
    del incomes[1]
    del savings[2]

    data = cast(Data, SimpleNamespace(incomes=incomes, savings=savings))
    actual = Service(main_user, data).chart_data()

    assert actual["percents"] == [200, 0, 0]
