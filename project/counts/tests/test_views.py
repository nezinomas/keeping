import re
import tempfile
from datetime import date

import pytest
from django.test import override_settings
from django.urls import resolve, reverse
from freezegun import freeze_time

from ...users.views import Login
from .. import forms, views
from ..factories import CountFactory, CountTypeFactory
from ..models import Count, CountType

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                     Count Create/Update
# ---------------------------------------------------------------------------------------
@override_settings(MEDIA_ROOT=tempfile.gettempdir())
@freeze_time('2000-01-01')
def test_view_new_form_initial(client_logged):
    x = CountTypeFactory()

    url = reverse('counts:new', kwargs={'slug': x.slug})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert '<input type="text" name="date" value="1999-01-01"' in actual
    assert '<input type="number" name="quantity" value="1"' in actual


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_view_new(client_logged):
    obj = CountTypeFactory()

    data = {
        'date': '1999-01-01',
        'quantity': 68,
        'count_type': obj.pk,
    }
    url = reverse('counts:new', kwargs={'slug': 'count-type'})
    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode("utf-8")

    assert '68' in actual
    assert '<a role="button" hx-get="/counts/update/1/"' in actual


def test_view_new_invalid_data(client_logged):
    data = {'date': -2, 'quantity': 'x'}

    url = reverse('counts:new', kwargs={'slug': 'count-type'})

    response = client_logged.post(url, data)
    form = response.context['form']

    assert not form.is_valid()


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_view_update(client_logged):
    t = CountTypeFactory()
    p = CountFactory()

    data = {
        'date': '1999-01-01',
        'quantity': 68,
        'count_type': t.pk,
    }
    url = reverse('counts:update', kwargs={'pk': p.pk})
    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode("utf-8")

    assert response.resolver_match.func.view_class is views.Lists

    assert '68' in actual
    assert f'<a role="button" hx-get="/counts/update/{p.pk}/"' in actual
    assert f'<a role="button" hx-get="/counts/delete/{p.pk}/"' in actual


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_view_update_not_load_other_user(client_logged, second_user):
    CountFactory()
    obj = CountFactory(date=date(1998, 12, 12), quantity=666, user=second_user)

    url = reverse('counts:update', kwargs={'pk': obj.pk})
    response = client_logged.get(url)
    form = response.content.decode()

    assert str(obj.quantity) not in form
    assert str(obj.date) not in form


# ---------------------------------------------------------------------------------------
#                                                                            Count Delete
# ---------------------------------------------------------------------------------------
def test_view_delete_func():
    view = resolve('/counts/delete/1/')

    assert views.Delete is view.func.view_class


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_view_delete_200(client_logged):
    p = CountFactory()

    url = reverse('counts:delete', kwargs={'pk': p.pk})
    response = client_logged.get(url)

    assert response.status_code == 200


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_view_delete_load_form(client_logged):
    p = CountFactory()

    url = reverse('counts:delete', kwargs={'pk': p.pk})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert f'<form method="POST" hx-post="{url}"' in actual
    assert 'Ar tikrai norite ištrinti: <strong>1999-01-01: 1.0</strong>?' in actual


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_view_delete(client_logged):
    p = CountFactory()
    assert Count.objects.all().count() == 1

    url = reverse('counts:delete', kwargs={'pk': p.pk})
    response = client_logged.post(url)

    assert response.status_code == 204
    assert Count.objects.all().count() == 0


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_view_delete_other_user_get_form(client_logged, second_user):
    obj = CountFactory(user=second_user)

    url = reverse('counts:delete', kwargs={'pk': obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_view_delete_other_user_post_form(client_logged, second_user):
    obj = CountFactory(user=second_user)

    url = reverse('counts:delete', kwargs={'pk': obj.pk})
    client_logged.post(url)

    assert Count.objects.all().count() == 1


# ---------------------------------------------------------------------------------------
#                                                                           Redirect View
# ---------------------------------------------------------------------------------------
def test_redirect_func():
    view = resolve('/counts/')

    assert views.Dispatch == view.func.view_class


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_redirect_redirect_to_index(client_logged):
    CountTypeFactory()

    url = reverse('counts:redirect')
    response = client_logged.get(url, follow=True)

    assert response.status_code == 200
    assert views.Index == response.resolver_match.func.view_class


def test_redirect_view_class(client_logged):
    url = reverse('counts:redirect')
    response = client_logged.get(url)

    assert views.Redirect == response.resolver_match.func.view_class


@pytest.mark.disable_get_user_patch
def test_redirect_user_not_logged(client):
    url = reverse('counts:redirect')
    response = client.get(url, follow=True)

    assert response.resolver_match.func.view_class is Login


# ---------------------------------------------------------------------------------------
#                                                                              Index View
# ---------------------------------------------------------------------------------------
def test_index_func():
    view = resolve('/counts/index/xxx/')

    assert views.Index == view.func.view_class


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_index_200(client_logged):
    obj = CountTypeFactory()

    url = reverse('counts:index', kwargs={'slug': obj.slug})
    response = client_logged.get(url)

    assert response.status_code == 200


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_index_add_button(client_logged):
    CountTypeFactory()

    url = reverse('counts:index', kwargs={'slug': 'count-type'})
    response = client_logged.get(url)
    content = response.content.decode()

    pattern = re.compile(r'<button type="button" class="btn.+hx-get="(.*?)".+ (\w+)<\/button>')
    res = re.findall(pattern, content)

    assert len(res[0]) == 2
    assert res[0][0] == reverse('counts:new', kwargs={'slug': 'count-type'})
    assert res[0][1] == 'Įrašą'


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_index_links(client_logged):
    CountTypeFactory(title='Xxx')

    url = reverse('counts:index', kwargs={'slug': 'xxx'})

    response = client_logged.get(url)

    content = response.content.decode()

    pattern = re.compile(r'<a href="(.*?)" class="btn btn-sm.+>(\w+)<\/a>')
    res = re.findall(pattern, content)

    assert len(res) == 3
    assert res[0][0] == reverse('counts:index', kwargs={'slug': 'xxx'})
    assert res[0][1] == 'Grafikai'

    assert res[1][0] == reverse('counts:list', kwargs={'slug': 'xxx'})
    assert res[1][1] == 'Duomenys'

    assert res[2][0] == reverse('counts:history', kwargs={'slug': 'xxx'})
    assert res[2][1] == 'Istorija'


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_index_context(client_logged):
    CountTypeFactory(title='Xxx')

    url = reverse('counts:index', kwargs={'slug': 'xxx'})
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

    url = reverse('counts:index', kwargs={'slug': 'xxx'})
    response = client_logged.get(url)

    assert response.context['tab'] == 'index'


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_index_chart_weekdays(client_logged):
    CountFactory()

    url = reverse('counts:index', kwargs={'slug': 'count-type'})
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    assert 'id="chart_weekdays"><div id="chart_weekdays_container"></div>' in content


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_index_chart_months(client_logged):
    CountFactory()

    url = reverse('counts:index', kwargs={'slug': 'count-type'})
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    assert 'id="chart_months"><div id="chart_months_container"></div>' in content


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_index_chart_histogram(client_logged):
    CountFactory()

    url = reverse('counts:index', kwargs={'slug': 'count-type'})
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    assert 'id="chart_histogram"><div id="chart_histogram_container"></div>' in content


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
@freeze_time('1999-07-18')
def test_index_info_row(client_logged):
    CountFactory(quantity=3)

    url = reverse('counts:index', kwargs={'slug': 'count-type'})
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    pattern = re.compile(r'Kiek:.+(\d+).+Savaitė.+(\d+).+Per savaitę.+([\d,]+)')

    for m in re.finditer(pattern, content):
        assert m.group(1) == 3
        assert m.group(2) == 28
        assert m.group(3) == '0,1'


@freeze_time('1999-1-1')
@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_index_info_row_latest_form_past(client_logged):
    CountFactory(date=date(1998, 1, 1))
    CountFactory(date=date(1999, 1, 2))

    url = reverse('counts:index', kwargs={'slug': 'count-type'})
    response = client_logged.get(url)
    context = response.context

    assert "'1999-01-02', 1.0, 366.0]" in context['chart_calendar_1H']


# ---------------------------------------------------------------------------------------
#                                                                              List View
# ---------------------------------------------------------------------------------------
def test_list_func():
    view = resolve('/counts/list/xxx/')

    assert views.Lists is view.func.view_class


def test_list_200(client_logged):
    obj = CountTypeFactory()
    url = reverse('counts:list', kwargs={'slug': obj.slug})
    response = client_logged.get(url)

    assert response.status_code == 200
    assert response.resolver_match.func.view_class is views.Lists


def test_list_empty_200(client_logged):
    url = reverse('counts:list', kwargs={'slug': 'xxx'})
    response = client_logged.get(url, follow=True)

    assert response.status_code == 200
    assert response.resolver_match.func.view_class is views.Empty


def test_list_context(client_logged):
    CountFactory()

    url = reverse('counts:list', kwargs={'slug': 'count-type'})
    response = client_logged.get(url)

    assert 'object_list' in response.context
    assert 'info_row' in response.context
    assert 'tab' in response.context
    assert 'list' == response.context['tab']


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_list(client_logged):
    p = CountFactory(quantity=66)
    url = reverse('counts:list', kwargs={'slug': 'count-type'})
    response = client_logged.get(url)

    actual = response.content.decode("utf-8")

    assert '66' in actual
    assert f'<a role="button" hx-get="/counts/update/{p.pk}/"' in actual


def test_list_no_data(client_logged):
    CountTypeFactory()

    url = reverse('counts:list', kwargs={'slug': 'count-type'})
    response = client_logged.get(url, follow=True)
    actual = response.content.decode("utf-8")

    assert '<b>1999</b> metais įrašų nėra.' in actual


# ---------------------------------------------------------------------------------------
#                                                                            History View
# ---------------------------------------------------------------------------------------
def test_history_func():
    view = resolve('/counts/history/xxx/')

    assert views.History == view.func.view_class


def test_history_200(client_logged):
    obj = CountTypeFactory()
    url = reverse('counts:history', kwargs={'slug': obj.slug})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_history_no_count_type(client_logged):
    url = reverse('counts:history', kwargs={'slug': 'xxx'})
    response = client_logged.get(url, follow=True)

    assert response.resolver_match.func.view_class is views.Empty


def test_history_context(client_logged):
    obj = CountTypeFactory()

    url = reverse('counts:history', kwargs={'slug': obj.slug})
    response = client_logged.get(url)

    assert 'tab' in response.context
    assert 'history' in response.context['tab']
    assert 'info_row' in response.context
    assert 'chart_weekdays' in response.context
    assert 'chart_years' in response.context
    assert 'chart_histogram' in response.context


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_history_chart_weekdays(client_logged):
    obj = CountTypeFactory()
    CountFactory()

    url = reverse('counts:history', kwargs={'slug': obj.slug})
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    assert '<div id="chart_weekdays_container"></div>' in content


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_history_chart_years(client_logged):
    obj = CountTypeFactory()
    CountFactory()

    url = reverse('counts:history', kwargs={'slug': obj.slug})
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    assert '<div id="chart_years_container"></div>' in content


# ---------------------------------------------------------------------------------------
#                                                                 CountType Create/Update
# ---------------------------------------------------------------------------------------
def test_count_type_new_func():
    view = resolve('/counts-type/new/')

    assert views.TypeNew is view.func.view_class


def test_count_type_update_func():
    view = resolve('/counts-type/update/1/')

    assert views.TypeUpdate is view.func.view_class


def test_count_type_new_200(client_logged):
    url = reverse('counts:type_new')
    response = client_logged.get(url)

    assert response.status_code == 200


def test_count_type_load_form(client_logged):
    obj = CountTypeFactory()

    url = reverse('counts:type_update', kwargs={'pk': obj.pk})
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert 'Count Type' in content


def test_count_type_form(client_logged):
    url = reverse('counts:type_new')
    response = client_logged.get(url)
    form = response.context.get('form')

    assert isinstance(form, forms.CountTypeForm)


def test_count_type_form_fields(client_logged):
    url = reverse('counts:type_new')
    response = client_logged.get(url)
    actual = response.content.decode()

    assert actual.count('<input') == 2
    assert actual.count('<button') == 4
    assert 'type="hidden" name="csrfmiddlewaretoken"' in actual
    assert '<input type="text" name="title"' in actual


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_count_type_new_valid_data(client_logged):
    data = {'title': 'XXX'}
    url = reverse('counts:type_new')
    client_logged.post(url, data, follow=True)

    actual = CountType.objects.first()
    assert actual.title == 'XXX'


def test_count_type_new_invalid_data(client_logged):
    data = {'title': 'X'}
    url = reverse('counts:type_new')
    response = client_logged.post(url, data)
    form = response.context.get('form')

    assert not form.is_valid()


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_count_type_update(client_logged):
    obj = CountFactory()

    data = {'title': 'YYY'}
    url = reverse('counts:type_update', kwargs={'pk': obj.pk})
    client_logged.post(url, data, follow=True)

    assert CountType.objects.count() == 1
    assert CountType.objects.first().title == 'YYY'


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_count_type_update_not_load_other_user(client_logged, second_user):
    obj = CountTypeFactory(title='xxx', user=second_user)

    url = reverse('counts:type_update', kwargs={'pk': obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


# ---------------------------------------------------------------------------------------
#                                                                        CountType Delete
# ---------------------------------------------------------------------------------------
def test_count_types_delete_func():
    view = resolve('/counts-type/delete/1/')

    assert views.TypeDelete is view.func.view_class


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_count_type_delete_200(client_logged):
    obj = CountTypeFactory()

    url = reverse('counts:type_delete', kwargs={'pk': obj.pk})

    response = client_logged.get(url)

    assert response.status_code == 200


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_count_type_delete_load_form(client_logged):
    obj = CountTypeFactory()

    url = reverse('counts:type_delete', kwargs={'pk': obj.pk})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert f'<form method="POST" hx-post="{url}"' in actual
    assert 'Ar tikrai norite ištrinti: <strong>Count Type</strong>?' in actual


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_count_type_delete(client_logged):
    _type = CountTypeFactory()
    _obj = CountFactory(count_type=_type)

    url = reverse('counts:type_delete', kwargs={'pk': _obj.pk})

    response = client_logged.post(url)

    assert CountType.objects.count() == 0
    assert Count.objects.count() == 0


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_count_type_delete_other_user_get_form(client_logged, second_user):
    obj = CountTypeFactory(user=second_user)

    url = reverse('counts:type_delete', kwargs={'pk': obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_count_type_delete_other_user_post_form(client_logged, second_user):
    obj = CountTypeFactory(user=second_user)

    url = reverse('counts:type_delete', kwargs={'pk': obj.pk})
    client_logged.post(url)

    assert CountType.objects.all().count() == 1


# ---------------------------------------------------------------------------------------
#                                                                          Count Redirect
# ---------------------------------------------------------------------------------------
def test_redirect_func():
    view = resolve('/counts/')

    assert views.Redirect is view.func.view_class


def test_redirect_no_counts(client_logged):
    url = reverse('counts:redirect')
    response = client_logged.get(url, follow=True)

    assert response.resolver_match.func.view_class is views.Empty


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_redirect_count_first(client_logged):
    CountTypeFactory(title='XXX')
    CountTypeFactory(title='AAA')

    url = reverse('counts:redirect')
    response = client_logged.get(url, follow=True)

    assert response.resolver_match.func.view_class is views.Index
    assert '<h6 class="me-3">AAA</h6>' in response.content.decode('utf-8')


# ---------------------------------------------------------------------------------------
#                                                                            Counts Empty
# ---------------------------------------------------------------------------------------
def test_empty_func():
    view = resolve('/counts/none/')

    assert views.Empty is view.func.view_class


def test_empty_200(client_logged):
    url = reverse('counts:empty')
    response = client_logged.get(url)

    assert response.status_code == 200

    actual = response.content.decode('utf-8')
    assert 'Jūs neturite skaitiklių.' in actual


@pytest.mark.disable_get_user_patch
def test_empty_user_not_logged(client):
    url = reverse('counts:empty')
    response = client.get(url, follow=True)

    assert response.resolver_match.func.view_class is Login
