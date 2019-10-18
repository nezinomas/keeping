from types import SimpleNamespace

import pytest
from mock import Mock, patch

from ..mixins.formset import FormsetMixin
from .utils import setup_view


@pytest.fixture()
def _request(rf):
    request = rf.get('/fake/')

    return request


def test_get_type_model_type_model_not_set(_request):
    class Dummy(FormsetMixin):
        type_model = None
        model = Mock(return_value='Model')()
        form_class = Mock()

    view = setup_view(Dummy(), _request)

    actual = view._get_type_model()

    assert 'Model' == actual


def test_get_type_model_type_model_is_set(_request):
    class Dummy(FormsetMixin):
        type_model = Mock(return_value='Type')()
        model = Mock(return_value='Model')()
        form_class = Mock()

    view = setup_view(Dummy(), _request)

    actual = view._get_type_model()

    assert 'Type' == actual


def test_model_type_without_foreignkey(_request):
    mck = Mock()
    mck._meta.get_fields.return_value = [
        SimpleNamespace(name='F', many_to_one=False)
    ]

    class Dummy(FormsetMixin):
        type_model = None
        model = mck
        form_class = Mock()

    view = setup_view(Dummy(), _request)

    actual = view._formset_initial()

    assert not actual


@patch('project.core.mixins.formset.FormsetMixin._get_type_model')
def test_model_type_items_is_called(mocked_model, _request):
    mocked_items = Mock()
    mocked_items.objects.items.return_value = ['XXX']

    mocked_model.return_value = mocked_items

    mck = Mock()
    mck._meta.get_fields.return_value = [
        SimpleNamespace(name='F', many_to_one=True)
    ]

    class Dummy(FormsetMixin):
        type_model = None
        model = mck
        form_class = Mock()

    view = setup_view(Dummy(), _request)

    actual = view._formset_initial()

    assert 1 == mocked_items.objects.items.call_count

    assert 1 == len(actual)
    assert 'XXX' == actual[0]['F']
