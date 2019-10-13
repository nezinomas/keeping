import json
from types import SimpleNamespace

import mock
import pytest
from django.views.generic import CreateView
from django.views.generic.edit import FormMixin

from ..mixins.ajax import AjaxCreateUpdateMixin
from .utils import setup_view


@pytest.fixture()
def _request(rf):
    request = rf.get('/fake/')
    request.resolver_match = SimpleNamespace(app_name='app_name')

    return request


@pytest.fixture()
def _ajax_request(rf):
    request = rf.get('/fake/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    request.resolver_match = SimpleNamespace(app_name='app_name')

    return request


def test_template_names_set_automatically(_request):
    mck = mock.MagicMock()
    mck._meta.verbose_name = 'plural'

    class Dummy(AjaxCreateUpdateMixin):
        template_name = None
        model = mck

    view = setup_view(Dummy(), _request)

    actual = view.get_template_names()
    expect = 'app_name/includes/plurals_form.html'

    assert actual[0] == expect


def test_template_names(_request):
    class Dummy(AjaxCreateUpdateMixin):
        template_name = 'XXX'
        model = mock.MagicMock()

    view = setup_view(Dummy(), _request)

    actual = view.get_template_names()
    expect = 'XXX'

    assert actual[0] == expect


def test_lists_template_names_set_automatically(_request):
    mck = mock.MagicMock()
    mck._meta.verbose_name = 'plural'

    class Dummy(AjaxCreateUpdateMixin):
        template_name = None
        model = mck

    view = setup_view(Dummy(), _request)

    actual = view._get_list_template_name()
    expect = 'app_name/includes/plurals_list.html'

    assert actual == expect


def test_lists_template_names(_request):
    class Dummy(AjaxCreateUpdateMixin):
        list_template_name = 'XXX'
        model = mock.MagicMock()

    view = setup_view(Dummy(), _request)

    actual = view._get_list_template_name()
    expect = 'XXX'

    assert actual == expect


@mock.patch('project.core.mixins.ajax.AjaxCreateUpdateMixin.get_context_data')
@mock.patch('project.core.mixins.ajax.render_to_string')
def test_form_valid_render(mck_render, mck_context, _request):
    class Dummy(AjaxCreateUpdateMixin, FormMixin):
        list_template_name = 'XXX'
        template_name = 'YYY'
        model = mock.MagicMock()

        def success_url(self):
            return ''

    mck_form = mock.MagicMock()
    mck_form.is_valid.return_value = True

    view = setup_view(Dummy(), _request)

    response = view.form_valid(mck_form)

    assert 2 == mck_render.call_count
    assert 1 == mck_context.call_count

    assert 302 == response.status_code


@mock.patch('project.core.mixins.ajax.AjaxCreateUpdateMixin.get_context_data')
@mock.patch('project.core.mixins.ajax.render_to_string')
def test_form_valid_ajax_response(mck_render, mck_context, _ajax_request):
    class Dummy(AjaxCreateUpdateMixin, FormMixin):
        list_template_name = 'XXX'
        template_name = 'YYY'
        model = mock.MagicMock()

    mck_render.side_effect = ['html_list', 'html_form']

    mck_form = mock.MagicMock()
    mck_form.is_valid.return_value = True

    view = setup_view(Dummy(), _ajax_request)
    response = view.form_valid(mck_form)

    assert 200 == response.status_code

    json_str = response.content
    actual = json.loads(json_str)

    assert 'html_list' == actual['html_list']
    assert 'html_form' == actual['html_form']


@mock.patch('project.core.mixins.ajax.AjaxCreateUpdateMixin.get_context_data')
def test_form_invalid_render(mck_context, _request):
    class Dummy(AjaxCreateUpdateMixin, CreateView):
        list_template_name = 'XXX'
        template_name = 'YYY'
        model = mock.MagicMock()

    mck_form = mock.MagicMock()
    mck_form.is_valid.return_value = False

    view = setup_view(Dummy(), _request)

    response = view.form_invalid(mck_form)

    assert 200 == response.status_code


@mock.patch('project.core.mixins.ajax.AjaxCreateUpdateMixin.get_context_data')
@mock.patch('project.core.mixins.ajax.render_to_string')
def test_form_invalid_ajax_response(mck_render, mck_context, _ajax_request):
    class Dummy(AjaxCreateUpdateMixin, FormMixin):
        list_template_name = 'XXX'
        template_name = 'YYY'
        model = mock.MagicMock()

    mck_render.side_effect = ['html_form']

    mck_form = mock.MagicMock()
    mck_form.is_valid.return_value = False

    view = setup_view(Dummy(), _ajax_request)
    response = view.form_invalid(mck_form)

    assert 200 == response.status_code

    json_str = response.content
    actual = json.loads(json_str)

    assert 'html_form' == actual['html_form']
