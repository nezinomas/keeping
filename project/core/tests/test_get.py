import mock
import pytest
from django.views.generic.list import MultipleObjectMixin

from ...incomes.models import Income
from ..factories import UserFactory
from ..mixins.get import GetQuerysetMixin


@pytest.fixture()
def _request(rf):
    request = rf.get('/fake/')
    request.user = UserFactory.build()

    return request


class Dummy(GetQuerysetMixin, MultipleObjectMixin):
    def __init__(self, model, request, *args, **kwargs):
        self.model = model
        self.request = request


@mock.patch('project.incomes.models.Income')
def test_get_execute_objects_year(mock_obj, _request):
    mock_obj.objects = mock.MagicMock()

    mock_obj.objects.year = mock.MagicMock()
    mock_obj.objects.year.return_value = 1

    a = Dummy(mock_obj, _request)
    b = a.get_queryset()

    assert b == 1


@mock.patch('project.incomes.models.Income')
def test_get_execute_objects_items(mock_obj, _request):
    mock_obj.objects = mock.MagicMock()

    mock_obj.objects.year = mock.MagicMock()
    mock_obj.objects.year.side_effect = Exception('Unknown')

    mock_obj.objects.items = mock.MagicMock()
    mock_obj.objects.items.return_value = 2

    a = Dummy(mock_obj, _request).get_queryset()

    assert a == 2


@mock.patch('project.incomes.models.Income')
def test_get_exexute_objects_all(mock_obj, _request):
    mock_obj.objects = mock.MagicMock()

    mock_obj.objects.year = mock.MagicMock()
    mock_obj.objects.year.side_effect = Exception('Unknown1')

    mock_obj.objects.items = mock.MagicMock()
    mock_obj.objects.items.side_effect = Exception('Unknown2')

    mock_obj.objects.all = mock.MagicMock()
    mock_obj.objects.all.return_value = 3

    a = Dummy(mock_obj, _request).get_queryset()

    assert a == 3


@mock.patch('project.incomes.models.Income')
def test_get_context_data(mock_obj, _request):
    mock_obj.objects = mock.MagicMock()

    mock_obj.objects.year = mock.MagicMock()
    mock_obj.objects.year.return_value = 1

    a = Dummy(mock_obj, _request)
    b = a.get_context_data(**{})

    assert 'items' in b
    assert 1 == b['items']


@mock.patch('project.incomes.models.Income')
def test_get_context_data_changed_context_object_name(mock_obj, _request):
    mock_obj.objects = mock.MagicMock()

    mock_obj.objects.year = mock.MagicMock()
    mock_obj.objects.year.return_value = 1

    a = Dummy(mock_obj, _request)
    a.context_object_name = 'X'

    b = a.get_context_data(**{})

    assert 'X' in b
    assert 1 == b['X']
