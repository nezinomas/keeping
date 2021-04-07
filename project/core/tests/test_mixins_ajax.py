import json
from types import SimpleNamespace

import pytest
from django.views.generic import CreateView
from django.views.generic.edit import FormMixin, DeletionMixin
from mock import Mock, patch

from ..mixins.ajax import AjaxCreateUpdateMixin, AjaxDeleteMixin
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


# ---------------------------------------------------------------------------------------
#                                                                        AjaxCreateUpdate
# ---------------------------------------------------------------------------------------
def test_template_names_set_automatically(_request):
    mck = Mock()
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
        model = Mock()

    view = setup_view(Dummy(), _request)

    actual = view.get_template_names()
    expect = 'XXX'

    assert actual[0] == expect


def test_lists_template_names_set_automatically(_request):
    mck = Mock()
    mck._meta.verbose_name = 'plural'

    class Dummy(AjaxCreateUpdateMixin):
        template_name = None
        model = mck

    view = setup_view(Dummy(), _request)

    actual = view.get_list_template_name()
    expect = 'app_name/includes/plurals_list.html'

    assert actual == expect


def test_lists_template_names(_request):
    class Dummy(AjaxCreateUpdateMixin):
        list_template_name = 'XXX'
        model = Mock()

    view = setup_view(Dummy(), _request)

    actual = view.get_list_template_name()
    expect = 'XXX'

    assert actual == expect


@patch('project.core.mixins.ajax.AjaxCreateUpdateMixin.get_context_data')
@patch('project.core.mixins.ajax.render_to_string')
def test_form_valid_render(mck_render, mck_context, _request):
    class Dummy(AjaxCreateUpdateMixin, FormMixin):
        list_template_name = 'XXX'
        template_name = 'YYY'
        model = Mock()

        def success_url(self):
            return ''

    mck_form = Mock()
    mck_form.is_valid.return_value = True

    view = setup_view(Dummy(), _request)

    response = view.form_valid(mck_form)

    assert mck_render.call_count == 1
    assert mck_context.call_count == 1

    assert response.status_code == 302


@patch('project.core.mixins.ajax.AjaxCreateUpdateMixin.get_context_data')
@patch('project.core.mixins.ajax.render_to_string')
def test_form_valid_ajax_response(mck_render, mck_context, _ajax_request):
    class Dummy(AjaxCreateUpdateMixin, FormMixin):
        list_template_name = 'XXX'
        template_name = 'YYY'
        model = Mock()

    mck_render.side_effect = ['html_list', 'html_form']

    mck_form = Mock()
    mck_form.is_valid.return_value = True

    view = setup_view(Dummy(), _ajax_request)
    response = view.form_valid(mck_form)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['html_list'] == 'html_list'
    assert actual['html_form'] == 'html_form'


@patch('project.core.mixins.ajax.AjaxCreateUpdateMixin.get_context_data')
@patch('project.core.mixins.ajax.render_to_string')
def test_form_valid_ajax_response_list_not_rendered(mck_render, mck_context, _ajax_request):
    class Dummy(AjaxCreateUpdateMixin, FormMixin):
        list_render_output = False
        list_template_name = 'XXX'
        template_name = 'YYY'
        model = Mock()

    mck_render.side_effect = ['html_form']

    mck_form = Mock()
    mck_form.is_valid.return_value = True

    view = setup_view(Dummy(), _ajax_request)
    response = view.form_valid(mck_form)

    assert response.status_code == 200
    assert mck_render.call_count == 1

    json_str = response.content
    actual = json.loads(json_str)

    assert 'html_list' not in actual


@patch('project.core.mixins.ajax.AjaxCreateUpdateMixin.get_context_data')
def test_form_invalid_render(mck_context, _request):
    class Dummy(AjaxCreateUpdateMixin, CreateView):
        list_template_name = 'XXX'
        template_name = 'YYY'
        model = Mock()

    mck_form = Mock()
    mck_form.is_valid.return_value = False

    view = setup_view(Dummy(), _request)

    response = view.form_invalid(mck_form)

    assert response.status_code == 200


@patch('project.core.mixins.ajax.AjaxCreateUpdateMixin.get_context_data')
@patch('project.core.mixins.ajax.render_to_string')
def test_form_invalid_ajax_response(mck_render, mck_context, _ajax_request):
    class Dummy(AjaxCreateUpdateMixin, FormMixin):
        list_template_name = 'XXX'
        template_name = 'YYY'
        model = Mock()

    mck_render.side_effect = ['html_form']

    mck_form = Mock()
    mck_form.is_valid.return_value = False

    view = setup_view(Dummy(), _ajax_request)
    response = view.form_invalid(mck_form)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['html_form'] == 'html_form'


# ---------------------------------------------------------------------------------------
#                                                                              AjaxDelete
# ---------------------------------------------------------------------------------------
def test_delete_template_names_set_automatically(_request):
    mck = Mock()
    mck._meta.verbose_name = 'plural'

    class Dummy(AjaxDeleteMixin):
        template_name = None
        model = mck

    view = setup_view(Dummy(), _request)

    actual = view.get_template_names()
    expect = 'app_name/includes/plurals_delete_form.html'

    assert actual[0] == expect


def test_delete_template_names(_request):
    class Dummy(AjaxDeleteMixin):
        template_name = 'XXX'
        model = Mock()

    view = setup_view(Dummy(), _request)

    actual = view.get_template_names()
    expect = 'XXX'

    assert actual[0] == expect


def test_delete_lists_template_names_set_automatically(_request):
    mck = Mock()
    mck._meta.verbose_name = 'plural'

    class Dummy(AjaxDeleteMixin):
        template_name = None
        model = mck

    view = setup_view(Dummy(), _request)

    actual = view.get_list_template_name()
    expect = 'app_name/includes/plurals_list.html'

    assert actual == expect


def test_delete_lists_template_names(_request):
    class Dummy(AjaxDeleteMixin):
        list_template_name = 'XXX'
        model = Mock()

    view = setup_view(Dummy(), _request)

    actual = view.get_list_template_name()
    expect = 'XXX'

    assert actual == expect


@patch('project.core.mixins.ajax.render_to_string')
def test_delete_post_render_normal_request(mck_render, _request):
    class Dummy(AjaxDeleteMixin, DeletionMixin):
        list_template_name = 'XXX'
        template_name = 'YYY'
        model = Mock()

        def success_url(self):
            return ''

        def delete(self, *args, **kwargs):
            return 'ok'

    view = setup_view(Dummy(), _request)

    response = view.post(_request)

    assert response == 'ok'


@patch('project.core.mixins.ajax.AjaxDeleteMixin.get_object')
@patch('project.core.mixins.ajax.AjaxDeleteMixin.get_context_data')
@patch('project.core.mixins.ajax.render_to_string')
def test_delete_list_not_rendered(mck_render, mck_context, mck_object, _ajax_request):
    class Dummy(AjaxDeleteMixin, FormMixin):
        list_render_output = False
        list_template_name = 'XXX'
        template_name = 'YYY'
        model = Mock()

    mck_render.side_effect = ['html_form']

    view = setup_view(Dummy(), _ajax_request)
    response = view.post()

    assert response.status_code == 200
    assert mck_render.call_count == 0

    json_str = response.content
    actual = json.loads(json_str)

    assert 'html_list' not in actual
    assert actual['form_is_valid']
