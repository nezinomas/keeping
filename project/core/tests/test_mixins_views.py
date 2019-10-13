import mock
import pytest
from django.views.generic import View

from ..factories import UserFactory
from ..mixins.views import ListMixin
from .utils import setup_view


@pytest.fixture()
def _request(rf):
    request = rf.get('/fake/')
    request.user = UserFactory.build()

    return request


def test_template_names(_request):
    class DummyListMixin(ListMixin):
        template_name = 'T'

    v = setup_view(DummyListMixin(), _request)
    v.get_template_names()

    assert v.template_name == 'T'


@mock.patch('django.contrib.auth.mixins.LoginRequiredMixin.dispatch')
def test_views_mixin_dispatch(mck, _request):
    class DummyListMixin(ListMixin):
        pass

    v = setup_view(DummyListMixin(), _request)
    v.dispatch(_request)

    assert mck.assert_called_once


@mock.patch('project.core.mixins.views.ListMixin._render_to_string')
def test_views_mixin_dispatch_render_as_string(mck, _request):
    class DummyListMixin(ListMixin):
        template_name = 'T'

    v = setup_view(DummyListMixin(), _request)
    v.dispatch(_request, **{'as_string': True})

    assert mck.assert_called_once
