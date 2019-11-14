from types import SimpleNamespace

from mock import Mock, patch

from ..mixins.formset import FormsetMixin
from .utils import setup_view


def test_get_type_model_type_model_not_set(fake_request):
    class Dummy(FormsetMixin):
        type_model = None
        model = Mock(return_value='Model')()
        form_class = Mock()

    view = setup_view(Dummy(), fake_request)

    actual = view._get_type_model()

    assert actual == 'Model'


def test_get_type_model_type_model_is_set(fake_request):
    class Dummy(FormsetMixin):
        type_model = Mock(return_value='Type')()
        model = Mock(return_value='Model')()
        form_class = Mock()

    view = setup_view(Dummy(), fake_request)

    actual = view._get_type_model()

    assert actual == 'Type'


def test_model_type_without_foreignkey(fake_request):
    mck = Mock()
    mck._meta.get_fields.return_value = [
        SimpleNamespace(name='F', many_to_one=False)
    ]

    class Dummy(FormsetMixin):
        type_model = None
        model = mck
        form_class = Mock()

    view = setup_view(Dummy(), fake_request)

    actual = view._formset_initial()

    assert not actual


@patch('project.core.mixins.formset.FormsetMixin._get_type_model')
def test_model_type_items_is_called(mocked_model, fake_request):
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

    view = setup_view(Dummy(), fake_request)

    actual = view._formset_initial()

    assert mocked_items.objects.items.call_count == 1

    assert len(actual) == 1
    assert actual[0]['F'] == 'XXX'
