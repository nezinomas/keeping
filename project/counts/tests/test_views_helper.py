from datetime import date
from types import SimpleNamespace

import pytest
from django.views.generic import TemplateView
from mock import patch

from ...core.tests.utils import setup_view
from ...users.factories import UserFactory
from ..factories import Count, CountFactory, CountTypeFactory
from ..lib import views_helper as H

pytestmark = pytest.mark.django_db


@pytest.fixture()
def _rf(rf):
    request = rf.get('/fake/')
    request.user = UserFactory.build()
    request.resolver_match = SimpleNamespace(kwargs={'count_type': 'count-type'})
    return request



def test_get_object_no_object():
    obj = H.get_object({})

    assert obj.pk == 0
    assert obj.slug == 'counter'
    assert obj.title == 'Nerasta'


def test_get_object():
    obj = CountTypeFactory(title='Xxx')

    actual = H.get_object({'count_type': 'xxx'})

    assert actual.pk == obj.pk
    assert actual.slug == obj.slug
    assert actual.title == obj.title


# ---------------------------------------------------------------------------------------
#                                                                           Context Mixin
# ---------------------------------------------------------------------------------------
def test_context_mixin_get_year(_rf):
    class Dummy(H.ContextMixin):
        pass

    view = setup_view(Dummy(), _rf)

    assert view.get_year() == 1999


def test_context_mixin_get_year_overwrite(_rf):
    class Dummy(H.ContextMixin):
        def get_year(self):
            return 666

    view = setup_view(Dummy(), _rf)

    assert view.get_year() == 666


@patch('project.core.lib.utils.get_request_kwargs')
def test_context_mixin_get_qs_sum_by_day(mck, _rf):
    mck.return_value = 'count-type'

    CountFactory(date=date(1999, 1, 1))
    CountFactory(date=date(1999, 1, 1))

    class Dummy(H.ContextMixin):
        pass

    view = setup_view(Dummy(), _rf)

    assert list(view.get_qs()) == [{'c': 2, 'date': date(1999, 1, 1), 'qty': 2}]


@patch('project.core.lib.utils.get_request_kwargs')
def test_context_mixin_get_qs_overwrite(mck, _rf):
    mck.return_value = 'count-type'

    class Dummy(H.ContextMixin):
        def get_qs(self):
            return 'y'

    view = setup_view(Dummy(), _rf)

    assert view.get_qs() == 'y'


@patch('project.core.lib.utils.get_request_kwargs')
def test_context_mixin_helper_istance(mck, _rf):
    mck.return_value = 'count-type'
    class Dummy(H.ContextMixin, TemplateView):
        def get_context_data(self, **kwargs):
            ctx = super().get_context_data(**kwargs)
            return ctx

    view = setup_view(Dummy(), _rf)
    view.get_context_data()

    assert isinstance(view.helper, H.RenderContext)


@patch('project.core.lib.utils.get_request_kwargs')
def test_context_mixin_context_no_data(mck, _rf):
    mck.return_value = 'count-type'
    class Dummy(H.ContextMixin, TemplateView):
        pass

    view = setup_view(Dummy(), _rf)
    ctx = view.get_context_data()

    assert ctx['count_type_object'].pk == 0
    assert ctx['count_type_object'].slug == 'counter'
    assert ctx['count_type_object'].title == 'Nerasta'
    assert ctx['records'] == 0


@patch('project.core.lib.utils.get_request_kwargs')
def test_context_mixin_context(mck, _rf):
    obj = CountTypeFactory(title='Xxx')
    CountFactory(counter_type=obj.slug)

    mck.return_value = obj.slug

    class Dummy(H.ContextMixin, TemplateView):
        pass

    view = setup_view(Dummy(), _rf)
    ctx = view.get_context_data(**{'count_type': obj.slug})

    assert ctx['count_type_object'].pk == obj.pk
    assert ctx['count_type_object'].slug == obj.slug
    assert ctx['count_type_object'].title == obj.title
    assert ctx['records'] == 1
