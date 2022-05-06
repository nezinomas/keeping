import tempfile

import pytest
from django.test import override_settings
from django.views.generic import TemplateView
from mock import patch

from ...core.tests.utils import setup_view
from .. import models
from ..factories import CountFactory
from ..lib import views_helper as H

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                           Context Mixin
# ---------------------------------------------------------------------------------------
def test_context_mixin_get_year_overwrite(fake_request):
    class Dummy(H.ContextMixin):
        def get_year(self):
            return 666

    view = setup_view(Dummy(), fake_request)

    assert view.get_year() == 666


@patch('project.core.lib.utils.get_request_kwargs')
def test_context_mixin_get_qs_overwrite(mck, fake_request):
    mck.return_value = 'count-type'

    class Dummy(H.ContextMixin):
        def get_qs(self):
            return 'y'

    view = setup_view(Dummy(), fake_request)

    assert view.get_qs() == 'y'


@pytest.mark.xfail()
@patch('project.core.lib.utils.get_request_kwargs')
def test_context_mixin_context_no_data(mck, fake_request):
    mck.return_value = 'count-type'
    class Dummy(H.ContextMixin, TemplateView):
        pass

    view = setup_view(Dummy(), fake_request)
    view.get_context_data()


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
@patch('project.core.lib.utils.get_request_kwargs')
def test_context_mixin_context(mck, fake_request):
    mck.return_value = 'count-type'

    obj = CountFactory()

    class Dummy(H.ContextMixin, TemplateView):
        def get_year(self):
            return 1999

        def get_queryset(self):
            return models.Count.objects.items()

    view = setup_view(Dummy(), fake_request)
    view.kwargs['count_type'] = obj.count_type.slug

    ctx = view.get_context_data()

    assert ctx['records'] == 1
