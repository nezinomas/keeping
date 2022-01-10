import json
import re
import tempfile
from datetime import date

import pytest
from django.http import JsonResponse
from django.test import override_settings
from django.urls import resolve, reverse
from django.utils.text import slugify
from freezegun import freeze_time
from mock import patch

from ...journals.factories import JournalFactory
from ...users.factories import UserFactory
from ...users.views import Login
from .. import forms, views
from ..factories import CountFactory, CountTypeFactory
from ..models import Count, CountType

X_Req = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                     Count Create/Update
# ---------------------------------------------------------------------------------------
@override_settings(MEDIA_ROOT=tempfile.gettempdir())
@freeze_time('2000-01-01')
def test_view_new_form_initial(client_logged):
    x = CountTypeFactory()
    url = reverse('counts:counts_new', kwargs={'count_type': x.slug})

    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert response.status_code == 200
    assert '<input type="text" name="date" value="1999-01-01"' in actual['html_form']
    assert '<input type="number" name="quantity" value="1"' in actual['html_form']


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_view_new(client_logged):
    CountTypeFactory()

    data = {'date': '1999-01-01', 'quantity': 68}

    url = reverse('counts:counts_new', kwargs={'count_type': 'count-type'})

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '68' in actual['html_list']
    assert f'<a role="button" data-url="/counts/update/count-type/1/"' in actual['html_list']


def test_view_new_invalid_data(client_logged):
    data = {'date': -2, 'quantity': 'x'}

    url = reverse('counts:counts_new', kwargs={'count_type': 'count-type'})

    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)

    assert not actual['form_is_valid']


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_view_update(client_logged):
    CountTypeFactory()
    p = CountFactory()

    data = {'date': '1999-01-01', 'quantity': 68}
    url = reverse('counts:counts_update', kwargs={'pk': p.pk, 'count_type': 'count-type'})

    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert '68' in actual['html_list']
    assert f'<a role="button" data-url="/counts/update/count-type/{p.pk}/"' in actual['html_list']


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_view_update_not_load_other_user(client_logged, second_user):
    CountFactory()
    obj = CountFactory(date=date(1998, 12, 12), quantity=666, user=second_user)

    url = reverse('counts:counts_update', kwargs={'pk': obj.pk, 'count_type': 'count-type'})
    response = client_logged.get(url, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)
    form = actual['html_form']

    assert str(obj.quantity) not in form
    assert str(obj.date) not in form


# ---------------------------------------------------------------------------------------
#                                                                            Count Delete
# ---------------------------------------------------------------------------------------
def test_view_delete_func():
    view = resolve('/counts/delete/xxx/1/')

    assert views.Delete is view.func.view_class


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_view_delete_200(client_logged):
    p = CountFactory()

    url = reverse('counts:counts_delete', kwargs={'pk': p.pk, 'count_type': 'xxx'})

    response = client_logged.get(url)

    assert response.status_code == 200


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_view_delete_load_form(client_logged):
    p = CountFactory()

    url = reverse('counts:counts_delete', kwargs={'pk': p.pk, 'count_type': 'count-type'})
    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)
    actual = actual['html_form']

    assert response.status_code == 200
    assert '<form method="post"' in actual
    assert 'Ar tikrai norite ištrinti: <strong>1999-01-01: 1.0</strong>?' in actual


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_view_delete(client_logged):
    p = CountFactory()

    assert Count.objects.all().count() == 1
    url = reverse('counts:counts_delete', kwargs={'pk': p.pk, 'count_type': 'count-type'})

    response = client_logged.post(url, {}, **X_Req)

    assert response.status_code == 200

    assert Count.objects.all().count() == 0


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_view_delete_other_user_get_form(client_logged, second_user):
    obj = CountFactory(user=second_user)

    url = reverse('counts:counts_delete', kwargs={'pk': obj.pk, 'count_type': 'count-type'})
    response = client_logged.get(url, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)
    form = actual['html_form']

    assert 'SRSLY' in form


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_view_delete_other_user_post_form(client_logged, second_user):
    obj = CountFactory(user=second_user)

    url = reverse('counts:counts_delete', kwargs={'pk': obj.pk, 'count_type': 'count-type'})
    client_logged.post(url, **X_Req)

    assert Count.objects.all().count() == 1


# ---------------------------------------------------------------------------------------
#                                                                              Index View
# ---------------------------------------------------------------------------------------
def test_index_func():
    view = resolve('/counts/xxx/')

    assert views.Index == view.func.view_class


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_index_200(client_logged):
    obj = CountTypeFactory()

    url = reverse('counts:counts_index', kwargs={'count_type': obj.slug})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_index_not_load_drinks(client_logged):
    url = reverse('counts:counts_index', kwargs={'count_type': 'drinks'})
    response = client_logged.get(url, follow=True)

    assert views.CountsEmpty == response.resolver_match.func.view_class


def test_index_not_exists_count_type(client_logged):
    url = reverse('counts:counts_index', kwargs={'count_type': 'xxx'})
    response = client_logged.get(url, follow=True)

    assert views.CountsEmpty == response.resolver_match.func.view_class


@pytest.mark.disable_get_user_patch
def test_index_user_not_logged(client):
    url = reverse('counts:counts_index', kwargs={'count_type': 'xxx'})
    response = client.get(url, follow=True)

    assert response.resolver_match.func.view_class is Login


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_index_add_button(client_logged):
    CountTypeFactory(title='Xxx')

    url = reverse('counts:counts_index', kwargs={'count_type': 'xxx'})
    response = client_logged.get(url)

    content = response.content.decode()

    pattern = re.compile(r'<button type="button" class="btn.+data-url="(.*?)".+ (\w+)<\/button>')
    res = re.findall(pattern, content)

    assert len(res[0]) == 2
    assert res[0][0] == reverse('counts:counts_new', kwargs={'count_type': 'xxx'})
    assert res[0][1] == 'Įrašą'


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_index_links(client_logged):
    CountTypeFactory(title='Xxx')

    url = reverse('counts:counts_index', kwargs={'count_type': 'xxx'})

    response = client_logged.get(url)

    content = response.content.decode()

    pattern = re.compile(r'<a href="(.*?)" class="btn btn-sm.+>(\w+)<\/a>')
    res = re.findall(pattern, content)

    assert len(res) == 3
    assert res[0][0] == reverse('counts:counts_index', kwargs={'count_type': 'xxx'})
    assert res[0][1] == 'Grafikai'

    assert res[1][0] == reverse('counts:counts_list', kwargs={'count_type': 'xxx'})
    assert res[1][1] == 'Duomenys'

    assert res[2][0] == reverse('counts:counts_history', kwargs={'count_type': 'xxx'})
    assert res[2][1] == 'Istorija'


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_index_context(client_logged):
    CountTypeFactory(title='Xxx')

    url = reverse('counts:counts_index', kwargs={'count_type': 'xxx'})
    response = client_logged.get(url)

    assert 'chart_weekdays' in response.context
    assert 'chart_months' in response.context
    assert 'chart_calendar_1H' in response.context
    assert 'chart_calendar_2H' in response.context
    assert 'chart_histogram' in response.context
    assert 'info_row' in response.context
    assert 'tab' in response.context


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_index_context_tab_value(client_logged):
    CountTypeFactory(title='Xxx')

    url = reverse('counts:counts_index', kwargs={'count_type': 'xxx'})
    response = client_logged.get(url)

    assert response.context['tab'] == 'index'


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_index_chart_weekdays(client_logged):
    CountTypeFactory(title='Xxx')
    CountFactory(counter_type='xxx')

    url = reverse('counts:counts_index', kwargs={'count_type': 'xxx'})
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    assert 'id="chart_weekdays"><div id="chart_weekdays_container"></div>' in content


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_index_chart_months(client_logged):
    CountTypeFactory(title='Xxx')
    CountFactory(counter_type='xxx')

    url = reverse('counts:counts_index', kwargs={'count_type': 'xxx'})
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    assert 'id="chart_months"><div id="chart_months_container"></div>' in content


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_index_chart_histogram(client_logged):
    CountTypeFactory(title='Xxx')
    CountFactory(counter_type='xxx')

    url = reverse('counts:counts_index', kwargs={'count_type': 'xxx'})
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    assert 'id="chart_histogram"><div id="chart_histogram_container"></div>' in content


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
@freeze_time('1999-07-18')
def test_index_info_row(client_logged):
    t = CountTypeFactory()
    CountFactory(quantity=3, counter_type=t.slug)

    url = reverse('counts:counts_index', kwargs={'count_type': t.slug})
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    pattern = re.compile(r'Kiek:.+(\d+).+Savaitė.+(\d+).+Per savaitę.+([\d,]+)')

    for m in re.finditer(pattern, content):
        assert m.group(1) == 3
        assert m.group(2) == 28
        assert m.group(3) == '0,1'


# ---------------------------------------------------------------------------------------
#                                                                            Realod Stats
# ---------------------------------------------------------------------------------------
def test_reload_stats_func():
    view = resolve('/counts/reload_stats/xxx/')

    assert views.ReloadStats == view.func.view_class


@patch('project.core.lib.utils.get_request_kwargs', return_value='xxx')
def test_reload_stats_render(mck, rf, get_user):
    request = rf.get('/counts/reload_stats/xxx/?ajax_trigger=1')
    request.user = UserFactory.build()
    request.user.journal = JournalFactory.build()

    response = views.ReloadStats.as_view()(request)

    assert response.status_code == 200


def test_reload_stats_jsonresponse_object(client_logged):
    url = reverse('counts:reload_stats', kwargs={'count_type': 'xxx'})
    response = client_logged.get(url, {'ajax_trigger': 1})

    assert isinstance(response, JsonResponse)


def test_reload_stats_render_ajax_trigger(client_logged):
    url = reverse('counts:reload_stats', kwargs={'count_type': 'xxx'})
    response = client_logged.get(url, {'ajax_trigger': 1})

    assert response.status_code == 200
    assert views.ReloadStats == response.resolver_match.func.view_class

    actual = json.loads(response.content)

    assert 'info_row' in actual
    assert 'chart_weekdays' in actual
    assert 'chart_months' in actual
    # assert 'chart_year' in actual
    assert 'chart_calendar_1H' in actual
    assert 'chart_calendar_2H' in actual
    assert 'chart_histogram' in actual


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_reload_stats_render_ajax_trigger_not_set(client_logged):
    CountTypeFactory(title='Xxx')

    url = reverse('counts:reload_stats', kwargs={'count_type': 'xxx'})
    response = client_logged.get(url, follow=True)

    assert response.status_code == 200
    assert views.Index == response.resolver_match.func.view_class


# ---------------------------------------------------------------------------------------
#                                                                              List View
# ---------------------------------------------------------------------------------------
def test_list_func():
    view = resolve('/counts/lists/xxx/')

    assert views.Lists == view.func.view_class


def test_list_200(client_logged):
    url = reverse('counts:counts_list', kwargs={'count_type': 'xxx'})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_list_context(client_logged):
    url = reverse('counts:counts_list', kwargs={'count_type': 'xxx'})
    response = client_logged.get(url)

    assert 'items' in response.context
    assert 'info_row' in response.context
    assert 'tab' in response.context


def test_list_context_tab_value(client_logged):
    url = reverse('counts:counts_list', kwargs={'count_type': 'xxx'})
    response = client_logged.get(url)

    assert response.context['tab'] == 'data'


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_list(client_logged):
    p = CountFactory(quantity=66)
    url = reverse('counts:counts_list', kwargs={'count_type': 'count-type'})
    response = client_logged.get(url)

    assert response.status_code == 200

    actual = response.content.decode("utf-8")

    assert '66' in actual
    assert f'<a role="button" data-url="/counts/update/count-type/{p.pk}/"' in actual


def test_list_empty(client_logged):
    url = reverse('counts:counts_list', kwargs={'count_type': 'count-type'})
    response = client_logged.get(url)

    assert response.status_code == 200

    actual = response.content.decode("utf-8")

    assert '<b>1999</b> metais įrašų nėra.' in actual


# ---------------------------------------------------------------------------------------
#                                                                            History View
# ---------------------------------------------------------------------------------------
def test_history_func():
    view = resolve('/counts/history/xxx/')

    assert views.History == view.func.view_class


def test_history_200(client_logged):
    url = reverse('counts:counts_history', kwargs={'count_type': 'xxx'})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_history_context(client_logged):
    url = reverse('counts:counts_history', kwargs={'count_type': 'xxx'})
    response = client_logged.get(url)

    assert 'chart_weekdays' in response.context
    assert 'chart_years' in response.context
    assert 'tab' in response.context


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_history_chart_weekdays(client_logged):
    CountFactory(counter_type='xxx')

    url = reverse('counts:counts_history', kwargs={'count_type': 'xxx'})
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    assert '<div id="chart_weekdays_container"></div>' in content


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_history_chart_years(client_logged):
    CountFactory(counter_type='xxx')

    url = reverse('counts:counts_history', kwargs={'count_type': 'xxx'})
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    assert '<div id="chart_years_container"></div>' in content


# ---------------------------------------------------------------------------------------
#                                                                 CountType Create/Update
# ---------------------------------------------------------------------------------------
def test_count_type_new_func():
    view = resolve('/counts/type/new/')

    assert views.TypeNew is view.func.view_class


def test_count_type_update_func():
    view = resolve('/counts/type/update/1/')

    assert views.TypeUpdate is view.func.view_class


def test_count_type_new_200(client_logged):
    url = reverse('counts:counts_type_new')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_count_type_update_200(client_logged):
    url = reverse('counts:counts_type_update', kwargs={'pk': 1})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_count_type_form(client_logged):
    url = reverse('counts:counts_type_new')

    response = client_logged.get(url, {}, **X_Req)

    form = response.context.get('form')

    assert isinstance(form, forms.CountTypeForm)


def test_count_type_form_fields(client_logged):
    url = reverse('counts:counts_type_new')

    response = client_logged.get(url, {}, **X_Req)
    json_str = response.content
    actual = json.loads(json_str)['html_form']

    assert actual.count('<input') == 2
    assert actual.count('<button') == 4
    assert 'type="hidden" name="csrfmiddlewaretoken"' in actual
    assert '<input type="text" name="title"' in actual


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_count_type_new_valid_data(client_logged):
    data = {'title': 'XXX'}
    url = reverse('counts:counts_type_new')
    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)
    assert actual['form_is_valid']

    actual = CountType.objects.first()
    assert actual.title == 'XXX'


def test_count_type_new_invalid_data(client_logged):
    data = {'title': 'X'}
    url = reverse('counts:counts_type_new')
    response = client_logged.post(url, data, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)
    assert not actual['form_is_valid']


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_count_type_update(client_logged):
    obj = CountTypeFactory(title='XXX')
    CountFactory(counter_type=slugify('XXX'))

    assert Count.objects.count() == 1
    assert Count.objects.first().counter_type == 'xxx'

    data = {'title': 'YYY'}
    url = reverse('counts:counts_type_update', kwargs={'pk': obj.pk})
    response = client_logged.post(url, data, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)

    assert actual['form_is_valid']
    assert CountType.objects.count() == 1
    assert CountType.objects.first().title == 'YYY'

    assert Count.objects.count() == 1
    assert Count.objects.first().counter_type == 'yyy'


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_count_type_update_not_load_other_user(client_logged, second_user):
    obj = CountTypeFactory(title='xxx', user=second_user)

    url = reverse('counts:counts_type_update', kwargs={'pk': obj.pk})
    response = client_logged.get(url, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)
    form = actual['html_form']

    assert obj.title not in form


# ---------------------------------------------------------------------------------------
#                                                                        CountType Delete
# ---------------------------------------------------------------------------------------
def test_count_types_delete_func():
    view = resolve('/counts/type/delete/1/')

    assert views.TypeDelete is view.func.view_class


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_count_type_delete_200(client_logged):
    obj = CountTypeFactory()

    url = reverse('counts:counts_type_delete', kwargs={'pk': obj.pk})

    response = client_logged.get(url)

    assert response.status_code == 200


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_count_type_delete_load_form(client_logged):
    obj = CountTypeFactory()

    url = reverse('counts:counts_type_delete', kwargs={'pk': obj.pk})
    response = client_logged.get(url, {}, **X_Req)

    json_str = response.content
    actual = json.loads(json_str)
    actual = actual['html_form']

    assert response.status_code == 200
    assert '<form method="post"' in actual
    assert 'Ar tikrai norite ištrinti: <strong>Count Type</strong>?' in actual


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
@patch('project.core.lib.utils.get_request_kwargs', return_value='xxx')
def test_count_type_delete(mck, client_logged):
    obj = CountTypeFactory(title='XXX')
    CountFactory(counter_type=slugify('XXX'))

    url = reverse('counts:counts_type_delete', kwargs={'pk': obj.pk})

    response = client_logged.post(url, {}, **X_Req)

    assert response.status_code == 200

    assert CountType.objects.count() == 0
    assert Count.objects.count() == 0


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_count_type_delete_no_patch(client_logged):
    obj = CountTypeFactory(title='XXX')
    CountFactory(counter_type=slugify('XXX'))

    url = reverse('counts:counts_type_delete', kwargs={'pk': obj.pk})

    response = client_logged.post(url, {}, **X_Req)

    assert response.status_code == 200

    assert CountType.objects.count() == 0
    assert Count.objects.count() == 0


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_count_type_delete_other_user_get_form(client_logged, second_user):
    obj = CountTypeFactory(user=second_user)

    url = reverse('counts:counts_type_delete', kwargs={'pk': obj.pk})
    response = client_logged.get(url, **X_Req)

    assert response.status_code == 200

    json_str = response.content
    actual = json.loads(json_str)
    form = actual['html_form']

    assert 'SRSLY' in form


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_count_type_delete_other_user_post_form(client_logged, second_user):
    obj = CountTypeFactory(user=second_user)

    url = reverse('counts:counts_type_delete', kwargs={'pk': obj.pk})
    client_logged.post(url, **X_Req)

    assert CountType.objects.all().count() == 1


# ---------------------------------------------------------------------------------------
#                                                                          Count Redirect
# ---------------------------------------------------------------------------------------
def test_redirect_func():
    view = resolve('/counts/redirect/0/')

    assert views.Redirect is view.func.view_class

def test_redirect_no_counts(client_logged):
    url = reverse('counts:counts_redirect', kwargs={'count_id': 0})
    response = client_logged.get(url, follow=True)

    assert response.resolver_match.func.view_class is views.CountsEmpty


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_redirect_count_first(client_logged):
    CountTypeFactory(title='XXX')

    url = reverse('counts:counts_redirect', kwargs={'count_id': 999})
    response = client_logged.get(url, follow=True)

    assert response.resolver_match.func.view_class is views.Index
    assert '<h6 class="me-3">XXX</h6>' in response.content.decode('utf-8')


# ---------------------------------------------------------------------------------------
#                                                                            Counts Empty
# ---------------------------------------------------------------------------------------
def test_empty_func():
    view = resolve('/counts/')

    assert views.CountsEmpty is view.func.view_class


def test_empty_200(client_logged):
    url = reverse('counts:counts_empty')
    response = client_logged.get(url)

    assert response.status_code == 200

    actual = response.content.decode('utf-8')
    assert 'Jūs neturite skaitiklių.' in actual


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_empty_redirect(client_logged):
    CountTypeFactory(title='XXX')

    url = reverse('counts:counts_empty')
    response = client_logged.get(url, follow=True)

    assert 'xxx' in response.request['PATH_INFO']


@pytest.mark.disable_get_user_patch
def test_empty_user_not_logged(client):
    url = reverse('counts:counts_empty')
    response = client.get(url, follow=True)

    assert response.resolver_match.func.view_class is Login
