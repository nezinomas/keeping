import tempfile
from datetime import date

import pytest
from django.test import override_settings
from django.views.generic import TemplateView
from mock import patch

from ...core.tests.utils import setup_view
from ..factories import CountFactory
from ..lib import views_helper as H

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                           Context Mixin
# ---------------------------------------------------------------------------------------
def test_context_mixin_get_year(fake_request):
    class Dummy(H.ContextMixin):
        pass

    view = setup_view(Dummy(), fake_request)

    assert view.get_year() == 1999


def test_context_mixin_get_year_overwrite(fake_request):
    class Dummy(H.ContextMixin):
        def get_year(self):
            return 666

    view = setup_view(Dummy(), fake_request)

    assert view.get_year() == 666


@patch('project.core.lib.utils.get_request_kwargs')
def test_context_mixin_get_qs_sum_by_day(mck, fake_request):
    mck.return_value = 'count-type'

    CountFactory(date=date(1999, 1, 1))
    CountFactory(date=date(1999, 1, 1))

    class Dummy(H.ContextMixin):
        pass

    view = setup_view(Dummy(), fake_request)

    assert list(view.get_queryset()) == [{'c': 2, 'date': date(1999, 1, 1), 'qty': 2}]


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
        pass

    view = setup_view(Dummy(), fake_request)
    view.kwargs['count_type'] = obj.count_type.slug

    ctx = view.get_context_data()

    assert ctx['object'] == obj.count_type
    assert ctx['records'] == 1
