from types import SimpleNamespace

from mock import Mock

from ...mixins.formset import FormsetMixin
from ..utils import setup_view


def test_model_type_without_foreignkey(fake_request):
    mck = Mock()
    mck._meta.get_fields.return_value = [SimpleNamespace(name="F", many_to_one=False)]

    class Dummy(FormsetMixin):
        model_service = None
        model = mck
        form_class = Mock()

    view = setup_view(Dummy(), fake_request)

    actual = view.formset_initial()

    assert not actual
