from datetime import date

import pytest
from mock import patch

from ..factories import BookFactory, BookTargetFactory
from ..services.chart_readed import ChartReaded

pytestmark = pytest.mark.django_db


def test_context_contains():
    obj = ChartReaded()
    actual = obj.context()

    assert 'categories' in actual
    assert 'data' in actual
    assert 'targets' in actual
    assert 'chart' in actual
    assert 'chart_title' in actual
    assert 'chart_column_color' in actual


def test_readed_property():
    BookFactory(started=date(1999, 1, 1), ended=date(1999, 1, 31))
    BookFactory(started=date(1999, 1, 1), ended=date(1999, 1, 31))

    obj = ChartReaded()
    actual = obj.readed

    assert actual == 1


@patch('project.books.services.chart_readed.ChartReaded._targets_list')
@patch('project.books.services.chart_readed.ChartReaded._get_readed')
def test_categories(mck_get_readed, mck_targets_list):
    mck_get_readed.return_value = [{'year': 1, 'cnt': 1}, {'year': 2, 'cnt': 2}]

    obj = ChartReaded()
    actual = obj.context()

    assert actual['categories'] == [1, 2]


@patch('project.books.services.chart_readed.ChartReaded._targets_list')
@patch('project.books.services.chart_readed.ChartReaded._get_readed')
def test_targets(mck_get_readed, mck_targets_list):
    mck_get_readed.return_value = [{'year': 11, 'cnt': 1}, {'year': 22, 'cnt': 2}]
    mck_targets_list.return_value = {11: 30}

    obj = ChartReaded()
    actual = obj.context()

    assert actual['targets'] == [30, 0]


@patch('project.books.services.chart_readed.ChartReaded._targets_list')
@patch('project.books.services.chart_readed.ChartReaded._get_readed')
def test_data(mck_get_readed, mck_targets_list):
    mck_get_readed.return_value = [{'year': 11, 'cnt': 1}, {'year': 22, 'cnt': 2}]
    mck_targets_list.return_value = {11: 30, 22: 40}

    obj = ChartReaded()
    actual = obj.context()

    assert actual['data'] == [{'y': 1, 'target': 30}, {'y': 2, 'target': 40}]


@patch('project.books.services.chart_readed.ChartReaded._targets_list')
@patch('project.books.services.chart_readed.ChartReaded._get_readed')
def test_chart_title(mck_get_readed, mck_targets_list):
    obj = ChartReaded()
    actual = obj.context()

    assert actual['chart_title'] == 'Perskaitytos knygos'


def test_target_list_returns_dict():
    BookTargetFactory(year=1, quantity=10)
    BookTargetFactory(year=2, quantity=20)

    obj = ChartReaded()
    actual = obj._targets_list()

    assert isinstance(actual, dict)
    assert actual == {1: 10, 2: 20}
