import mock

from ..mixins.views import ListMixin
from .utils import setup_view


def test_template_names(fake_request):
    class DummyListMixin(ListMixin):
        template_name = 'T'

    v = setup_view(DummyListMixin(), fake_request)
    v.get_template_names()

    assert v.template_name == 'T'


@mock.patch('django.contrib.auth.mixins.LoginRequiredMixin.dispatch')
def test_views_mixin_dispatch(mck, fake_request):
    class DummyListMixin(ListMixin):
        pass

    v = setup_view(DummyListMixin(), fake_request)
    v.dispatch(fake_request)

    assert mck.assert_called_once


@mock.patch('project.core.mixins.views.render_to_string')
def test_views_mixin_dispatch_render_as_string(mck, fake_request):
    class DummyListMixin(ListMixin):
        template_name = 'T'

    v = setup_view(DummyListMixin(), fake_request)
    v.dispatch(fake_request, **{'as_string': True})

    assert mck.assert_called_once
