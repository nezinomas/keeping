import mock
import pytest
from django.views.generic.edit import FormMixin
from django.views.generic.list import MultipleObjectMixin

from ...incomes.models import Income
from ..factories import UserFactory
from ..mixins.get import GetFormKwargsMixin, GetQuerysetMixin


@pytest.fixture()
def _request(rf):
    request = rf.get('/fake/')
    request.user = UserFactory.build()

    return request


class TestGetQueryset(GetQuerysetMixin, MultipleObjectMixin):
    def __init__(self, model, request, *args, **kwargs):
        self.model = model
        self.request = request


class TestFormKwargs(GetFormKwargsMixin, FormMixin):
    def __init__(self, request, *args, **kwargs):
        self.request = request


@mock.patch('project.incomes.models.Income')
def test_get_execute_objects_year(mock_obj, _request):
    mock_obj.objects = mock.MagicMock()
    mock_obj.objects.year.return_value = 1

    actual = TestGetQueryset(mock_obj, _request).get_queryset()

    assert actual == 1


@mock.patch('project.incomes.models.Income')
def test_get_execute_objects_items(mock_obj, _request):
    mock_obj.objects = mock.MagicMock()
    mock_obj.objects.year.side_effect = Exception('Unknown')
    mock_obj.objects.items.return_value = 2

    actual = TestGetQueryset(mock_obj, _request).get_queryset()

    assert actual == 2


@mock.patch('project.incomes.models.Income')
def test_get_exexute_objects_all(mock_obj, _request):
    mock_obj.objects = mock.MagicMock()
    mock_obj.objects.year.side_effect = Exception('Unknown1')
    mock_obj.objects.items.side_effect = Exception('Unknown2')
    mock_obj.objects.all.return_value = 3

    actual = TestGetQueryset(mock_obj, _request).get_queryset()

    assert actual == 3


@mock.patch('project.incomes.models.Income')
def test_get_execute_objects_month(mock_obj, _request):
    mock_obj.objects = mock.MagicMock()
    mock_obj.objects.month = mock.MagicMock()
    mock_obj.objects.month.return_value = 1

    obj = TestGetQueryset(mock_obj, _request)
    obj.month = True

    actual = obj.get_queryset()

    assert actual == 1


@mock.patch('project.incomes.models.Income')
def test_get_context_data(mock_obj, _request):
    mock_obj.objects = mock.MagicMock()
    mock_obj.objects.year.return_value = 1

    actual = TestGetQueryset(mock_obj, _request).get_context_data(**{})

    assert 'items' in actual
    assert 1 == actual['items']


@mock.patch('project.incomes.models.Income')
def test_get_context_data_changed_context_object_name(mock_obj, _request):
    mock_obj.objects = mock.MagicMock()
    mock_obj.objects.year.return_value = 1

    obj = TestGetQueryset(mock_obj, _request)
    obj.context_object_name = 'X'

    actual = obj.get_context_data(**{})

    assert 'X' in actual
    assert 1 == actual['X']


def test_get_form_kwargs(_request):
    actual = TestFormKwargs(_request).get_form_kwargs()

    assert 'year' in actual
    assert 1999 == actual['year']
