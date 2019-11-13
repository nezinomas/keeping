import mock
import pytest
from django.views.generic.list import MultipleObjectMixin

from ..mixins.get import GetQuerysetMixin


class GetQueryset(GetQuerysetMixin, MultipleObjectMixin):
    def __init__(self, model, request, *args, **kwargs):
        self.model = model
        self.request = request


@mock.patch('project.incomes.models.Income')
def test_get_execute_objects_year(mock_obj, _fake_request):
    mock_obj.objects = mock.MagicMock()
    mock_obj.objects.year.return_value = 1

    actual = GetQueryset(mock_obj, _fake_request).get_queryset()

    assert actual == 1


@mock.patch('project.incomes.models.Income')
def test_get_execute_objects_items(mock_obj, _fake_request):
    mock_obj.objects = mock.MagicMock()
    mock_obj.objects.year.side_effect = AttributeError
    mock_obj.objects.items.return_value = 2

    actual = GetQueryset(mock_obj, _fake_request).get_queryset()

    assert actual == 2


@mock.patch('project.incomes.models.Income')
def test_get_exexute_objects_all(mock_obj, _fake_request):
    mock_obj.objects = mock.MagicMock()
    mock_obj.objects.year.side_effect = AttributeError
    mock_obj.objects.items.side_effect = AttributeError

    actual = GetQueryset(mock_obj, _fake_request).get_queryset()

    assert actual == {}


@mock.patch('project.incomes.models.Income')
def test_get_context_data(mock_obj, _fake_request):
    mock_obj.objects = mock.MagicMock()
    mock_obj.objects.year.return_value = 1

    actual = GetQueryset(mock_obj, _fake_request).get_context_data(**{})

    assert 'items' in actual
    assert 1 == actual['items']


@mock.patch('project.incomes.models.Income')
def test_get_context_data_changed_context_object_name(mock_obj, _fake_request):
    mock_obj.objects = mock.MagicMock()
    mock_obj.objects.year.return_value = 1

    obj = GetQueryset(mock_obj, _fake_request)
    obj.context_object_name = 'X'

    actual = obj.get_context_data(**{})

    assert 'X' in actual
    assert 1 == actual['X']
