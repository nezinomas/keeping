import re
from datetime import date, datetime

import pytest
import time_machine
from django.urls import resolve, reverse

from ...users.views import Login
from .. import forms, views
from ..models import Count, CountType
from ..tabs import TABS
from .factories import CountFactory, CountTypeFactory

pytestmark = pytest.mark.django_db


# -------------------------------------------------------------------------------------
#                                                                   Count Create/Update
# -------------------------------------------------------------------------------------
def test_view_new_func():
    view = resolve("/counts/tab/xxx/new/")

    assert views.New is view.func.view_class


def test_view_update_func():
    view = resolve("/counts/update/1/")

    assert views.Update is view.func.view_class


@pytest.mark.parametrize(
    "tab_actual, tab_expected",
    [
        ("index", "index"),
        ("data", "data"),
        ("history", "history"),
        ("xxx", "index"),
    ],
)
def test_view_new_url(client_logged, tab_actual, tab_expected):
    x = CountTypeFactory()

    url = reverse("counts:new", kwargs={"slug": x.slug, "tab": tab_actual})
    response = client_logged.get(url)

    assert response.context["view"].url() == reverse(
        "counts:new", kwargs={"slug": x.slug, "tab": tab_expected}
    )


@pytest.mark.parametrize(
    "tab, expected",
    [
        ("index", "reloadIndex"),
        ("data", "reloadData"),
        ("history", "reloadHistory"),
        ("xxx", "reloadData"),
    ],
)
def test_view_new_get_hx_trigger_django(client_logged, tab, expected):
    x = CountTypeFactory()

    url = reverse("counts:new", kwargs={"slug": x.slug, "tab": tab})
    response = client_logged.get(url)

    assert response.context["view"].get_hx_trigger_django() == expected


def test_view_update_get_hx_trigger_django(client_logged):
    x = CountFactory()

    url = reverse("counts:update", kwargs={"pk": x.pk})
    response = client_logged.get(url)

    assert response.context["view"].get_hx_trigger_django() == "reloadData"


@pytest.mark.parametrize(
    "tab_sent, tab_actual",
    [
        ("index", "index"),
        ("data", "data"),
        ("history", "history"),
        ("xxx", "index"),
    ],
)
@time_machine.travel(datetime(2000, 1, 1))
def test_view_new_form_initial(client_logged, tab_sent, tab_actual):
    x = CountTypeFactory()

    url = reverse("counts:new", kwargs={"slug": x.slug, "tab": tab_sent})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    url = reverse("counts:new", kwargs={"slug": x.slug, "tab": tab_actual})

    assert '<form method="POST"' in actual
    assert f'hx-post="{url}"' in actual
    assert '<input type="text" name="date" value="1999-01-01"' in actual
    assert '<select name="count_type"' in actual
    assert '<input type="number" name="quantity" value="1"' in actual


def test_view_new(client_logged):
    obj = CountTypeFactory()

    data = {
        "date": "1999-01-01",
        "quantity": 68,
        "count_type": obj.pk,
    }
    url = reverse("counts:new", kwargs={"slug": "count-type", "tab": "data"})
    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode("utf-8")

    assert "68" in actual
    assert '<a role="button" hx-get="/counts/update/1/"' in actual
    assert '<a role="button" hx-get="/counts/delete/1/"' in actual


def test_view_new_load_form(client_logged):
    o1 = CountTypeFactory(title="XXX")
    o2 = CountTypeFactory(title="ZZZ")

    url = reverse("counts:new", kwargs={"slug": "zzz", "tab": "data"})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert f'hx-post="{url}"' in actual
    assert f'<option value="{o1.pk}">{o1.title}</option>' in actual
    assert f'<option value="{o2.pk}" selected>{o2.title}</option>' in actual


def test_view_new_invalid_data(client_logged):
    data = {"date": -2, "quantity": "x"}

    url = reverse("counts:new", kwargs={"slug": "count-type", "tab": "data"})

    response = client_logged.post(url, data)
    form = response.context["form"]

    assert not form.is_valid()


def test_view_update_load_form(client_logged):
    count_type_1 = CountTypeFactory(title="ZZZ")
    count_type_2 = CountTypeFactory(title="AAA")

    count = CountFactory(count_type=count_type_1)

    url = reverse("counts:update", kwargs={"pk": count.pk})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert f'hx-post="{url}"' in actual
    assert (
        f'<option value="{count_type_1.pk}" selected>{count_type_1.title}</option>'
        in actual
    )
    assert f'<option value="{count_type_2.pk}">{count_type_2.title}</option>' in actual


def test_view_update(client_logged):
    t = CountTypeFactory()
    p = CountFactory()

    data = {
        "date": "1999-01-01",
        "quantity": 68,
        "count_type": t.pk,
    }
    url = reverse("counts:update", kwargs={"pk": p.pk})
    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode("utf-8")

    assert response.resolver_match.func.view_class is views.TabData

    assert "68" in actual
    assert f'<a role="button" hx-get="/counts/update/{p.pk}/"' in actual
    assert f'<a role="button" hx-get="/counts/delete/{p.pk}/"' in actual


def test_view_update_not_load_other_user(client_logged, second_user):
    CountFactory()
    obj = CountFactory(date=date(1998, 12, 12), quantity=666, user=second_user)

    url = reverse("counts:update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)
    form = response.content.decode()

    assert str(obj.quantity) not in form
    assert str(obj.date) not in form


# -------------------------------------------------------------------------------------
#                                                                          Count Delete
# -------------------------------------------------------------------------------------
def test_view_delete_func():
    view = resolve("/counts/delete/1/")

    assert views.Delete is view.func.view_class


def test_view_delete_200(client_logged):
    p = CountFactory()

    url = reverse("counts:delete", kwargs={"pk": p.pk})
    response = client_logged.get(url)

    assert response.status_code == 200


@time_machine.travel(datetime(2000, 1, 1))
def test_view_delete_get_hx_trigger_django(client_logged):
    x = CountFactory()

    url = reverse("counts:delete", kwargs={"pk": x.pk})
    response = client_logged.get(url)

    assert response.context["view"].get_hx_trigger_django() == "reloadData"


def test_view_delete_load_form(client_logged):
    p = CountFactory()

    url = reverse("counts:delete", kwargs={"pk": p.pk})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert '<form method="POST"' in actual
    assert f'hx-post="{url}"' in actual
    assert "Ar tikrai norite ištrinti: <strong>1999-01-01: 1.0</strong>?" in actual


def test_view_delete(client_logged):
    p = CountFactory()
    assert Count.objects.all().count() == 1

    url = reverse("counts:delete", kwargs={"pk": p.pk})
    response = client_logged.post(url)

    assert response.status_code == 204
    assert Count.objects.all().count() == 0


def test_view_delete_other_user_get_form(client_logged, second_user):
    obj = CountFactory(user=second_user)

    url = reverse("counts:delete", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_view_delete_other_user_post_form(client_logged, second_user):
    obj = CountFactory(user=second_user)

    url = reverse("counts:delete", kwargs={"pk": obj.pk})
    client_logged.post(url)

    assert Count.objects.all().count() == 1


# -------------------------------------------------------------------------------------
#                                                                         Redirect View
# -------------------------------------------------------------------------------------
def test_redirect_func():
    view = resolve("/counts/")

    assert views.Redirect is view.func.view_class


def test_redirect_redirect_to_index(client_logged):
    CountTypeFactory()

    url = reverse("counts:redirect")
    response = client_logged.get(url, follow=True)

    assert response.status_code == 200
    assert views.TabIndex == response.resolver_match.func.view_class


def test_redirect_redirect_to_empty(client_logged):
    url = reverse("counts:redirect")
    response = client_logged.get(url, follow=True)

    assert response.status_code == 200
    assert views.Empty == response.resolver_match.func.view_class


@pytest.mark.disable_get_user_patch
def test_redirect_user_not_logged(client):
    url = reverse("counts:redirect")
    response = client.get(url, follow=True)

    assert response.resolver_match.func.view_class is Login


def test_redirect_no_counts(client_logged):
    url = reverse("counts:redirect")
    response = client_logged.get(url, follow=True)

    assert response.resolver_match.func.view_class is views.Empty


def test_redirect_count_first(client_logged):
    CountTypeFactory(title="XXX")
    CountTypeFactory(title="AAA")

    url = reverse("counts:redirect")
    response = client_logged.get(url, follow=True)

    assert response.resolver_match.func.view_class is views.TabIndex
    assert '<span class="counter-name">AAA</span>' in response.content.decode("utf-8")


# -------------------------------------------------------------------------------------
#                                                                            Index View
# -------------------------------------------------------------------------------------
def test_index_func():
    view = resolve("/counts/xxx/")

    assert views.TabIndex == view.func.view_class


def test_index_200(client_logged):
    obj = CountTypeFactory()

    url = reverse("counts:index", kwargs={"slug": obj.slug})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_index_not_logged(client):
    obj = CountTypeFactory()

    url = reverse("counts:index", kwargs={"slug": obj.slug})
    response = client.get(url)

    assert response.status_code == 302


def test_index_redirect_no_count_type(client_logged):
    url = reverse("counts:index", kwargs={"slug": "XXX"})
    response = client_logged.get(url, follow=True)

    assert views.Empty is response.resolver_match.func.view_class


def test_index_redirect(client_logged):
    obj = CountTypeFactory()

    url = reverse("counts:index", kwargs={"slug": "XXX"})
    response = client_logged.get(url, follow=True)

    assert views.TabIndex is response.resolver_match.func.view_class
    assert response.resolver_match.url_name == "index"
    assert response.resolver_match.kwargs["slug"] == obj.slug


def test_index_add_button(client_logged):
    CountTypeFactory()

    url = reverse("counts:index", kwargs={"slug": "count-type"})
    response = client_logged.get(url)
    content = response.content.decode()

    pattern = re.compile(
        r'<button type="button" class="button-outline-success" hx-get="(.*?)" .*?>(\w+)<\/button>'  # noqa: E501
    )
    res = re.findall(pattern, content)

    assert len(res[0]) == 2
    assert res[0][0] == reverse(
        "counts:new", kwargs={"slug": "count-type", "tab": "index"}
    )
    assert res[0][1] == "Įrašą"


def test_index_links(client_logged):
    CountTypeFactory(title="Xxx")

    url = reverse("counts:index", kwargs={"slug": "xxx"})
    content = client_logged.get(url).content.decode()

    for tab in TABS:
        assert f'hx-get="{tab.url("xxx")}"' in content
        assert str(tab.title) in content

    assert [str(tab.title) for tab in TABS] == ["Apžvalga", "Istorija", "Duomenys"]


def test_index_context(client_logged):
    CountTypeFactory(title="Xxx")

    url = reverse("counts:index", kwargs={"slug": "xxx"})
    response = client_logged.get(url)

    assert "object" in response.context
    assert "info_row" in response.context
    assert "content" in response.context


# -------------------------------------------------------------------------------------
#                                                                               Tab Nav
# -------------------------------------------------------------------------------------
@pytest.mark.parametrize("open_tab", [tab.name for tab in TABS])
def test_nav_marks_the_open_tab(client_logged, open_tab):
    CountTypeFactory(title="Xxx")

    url = reverse(f"counts:tab_{open_tab}", kwargs={"slug": "xxx"})
    content = client_logged.get(url).content.decode()

    assert content.count('role="tab"') == len(TABS)
    assert content.count('aria-selected="true"') == 1
    assert f'id="tab-{open_tab}"' in content
    assert re.search(rf'id="tab-{open_tab}"[^>]+aria-selected="true"', content)


def test_nav_tabs_push_their_url(client_logged):
    CountTypeFactory(title="Xxx")

    url = reverse("counts:index", kwargs={"slug": "xxx"})
    content = client_logged.get(url).content.decode()

    assert content.count('hx-push-url="true"') == len(TABS)


def test_the_page_has_no_header_and_names_the_counter_in_the_quick_add_bar(
    client_logged,
):
    CountTypeFactory(title="Xxx")

    url = reverse("counts:index", kwargs={"slug": "xxx"})
    content = client_logged.get(url).content.decode()

    assert "counts-title" not in content
    assert content.count('<span class="counter-name">Xxx</span>') == 1


def test_a_tab_url_visited_plainly_returns_the_whole_page(client_logged):
    CountTypeFactory(title="Xxx")

    url = reverse("counts:tab_history", kwargs={"slug": "xxx"})
    content = client_logged.get(url).content.decode()

    assert 'class="quick-add"' in content
    assert 'class="subnav"' in content


def test_a_tab_url_requested_by_htmx_returns_the_fragment_alone(client_logged):
    CountTypeFactory(title="Xxx")

    url = reverse("counts:tab_history", kwargs={"slug": "xxx"})
    content = client_logged.get(url, headers={"HX-Request": "true"}).content.decode()

    assert 'class="quick-add"' not in content
    assert 'class="subnav"' not in content


# -------------------------------------------------------------------------------------
#                                                                             Tab Index
# -------------------------------------------------------------------------------------
def test_tab_index_func():
    view = resolve("/counts/xxx/index/")

    assert views.TabIndex == view.func.view_class


def test_tab_index_chart_weekdays(client_logged):
    CountFactory()

    url = reverse("counts:tab_index", kwargs={"slug": "count-type"})
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    assert '<div id="chart-weekdays-container"></div>' in content


def test_tab_index_chart_months(client_logged):
    CountFactory()

    url = reverse("counts:index", kwargs={"slug": "count-type"})
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    assert '<div id="chart-months-container"></div>' in content


def test_tab_index_chart_histogram(client_logged):
    CountFactory()

    url = reverse("counts:index", kwargs={"slug": "count-type"})
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    assert '<div id="chart-histogram-container">' in content


@time_machine.travel(datetime(1999, 7, 18))
def test_index_info_row(client_logged):
    obj = CountFactory(quantity=3)

    url = reverse("counts:index", kwargs={"slug": obj.count_type.slug})
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    pattern = re.compile(r"Kiek:.+(\d+).+Savaitė.+(\d+).+Per savaitę.+([\d,]+)")

    for m in re.finditer(pattern, content):
        assert m.group(1) == 3
        assert m.group(2) == 28
        assert m.group(3) == "0,1"


@time_machine.travel(datetime(1999, 1, 1))
def test_index_calendar_replaces_the_heatmap_charts(client_logged):
    CountFactory()

    url = reverse("counts:index", kwargs={"slug": "count-type"})
    response = client_logged.get(url)

    assert "calendar" in response.context
    assert "chart_calendar_1H" not in response.context
    assert "chart_calendar_2H" not in response.context


@time_machine.travel(datetime(1999, 1, 1))
def test_index_calendar_gap_from_previous_year(client_logged):
    CountFactory(date=date(1998, 1, 1))
    CountFactory(date=date(1999, 1, 2))

    url = reverse("counts:index", kwargs={"slug": "count-type"})
    response = client_logged.get(url)
    january = response.context["calendar"].months[0]

    assert january.days[1].gap == 366


@time_machine.travel(datetime(1999, 1, 10))
def test_index_calendar_draws_presence_at_one_level(client_logged):
    CountFactory(date=date(1999, 1, 2), quantity=99)

    url = reverse("counts:index", kwargs={"slug": "count-type"})
    response = client_logged.get(url)
    january = response.context["calendar"].months[0]

    assert january.days[1].level == 1
    assert response.context["calendar"].legend.bounds == ("0", ">0")


def _gap_strip(content: str) -> str:
    return re.search(r'<div class="gap-strip".*?</div>', content, re.S).group()


@time_machine.travel(datetime(1999, 7, 1))
def test_index_gap_strip_draws_one_tick_a_day(client_logged):
    CountFactory(date=date(1999, 1, 2))
    CountFactory(date=date(1999, 3, 4))

    url = reverse("counts:index", kwargs={"slug": "count-type"})
    strip = _gap_strip(client_logged.get(url).content.decode("utf-8"))

    assert strip.count("<i") == 365
    assert strip.count('class="hit"') == 2


@time_machine.travel(datetime(2000, 7, 1))
def test_index_gap_strip_draws_a_leap_year(client_logged, main_user):
    main_user.year = 2000
    main_user.save()

    CountFactory(date=date(2000, 1, 2))

    url = reverse("counts:index", kwargs={"slug": "count-type"})
    strip = _gap_strip(client_logged.get(url).content.decode("utf-8"))

    assert strip.count("<i") == 366


@time_machine.travel(datetime(1999, 1, 10))
def test_index_calendar_empty_day_says_no_records(client_logged):
    CountFactory(date=date(1999, 1, 2))

    url = reverse("counts:index", kwargs={"slug": "count-type"})
    response = client_logged.get(url)
    january = response.context["calendar"].months[0]

    assert january.days[0].label == "1999-01-01\nĮrašų nėra"


# -------------------------------------------------------------------------------------
#                                                                              Tab List
# -------------------------------------------------------------------------------------
def test_data_func():
    view = resolve("/counts/xxx/data/")

    assert views.TabData is view.func.view_class


def test_data_200(client_logged):
    obj = CountTypeFactory()
    url = reverse("counts:tab_data", kwargs={"slug": obj.slug})
    response = client_logged.get(url)

    assert response.status_code == 200
    assert response.resolver_match.func.view_class is views.TabData


def test_data_context(client_logged):
    CountFactory()

    url = reverse("counts:tab_data", kwargs={"slug": "count-type"})
    response = client_logged.get(url)

    assert "object_list" in response.context
    assert "slug" in response.context
    assert response.context["slug"] == "count-type"


def test_data(client_logged):
    p = CountFactory(quantity=66)
    url = reverse("counts:tab_data", kwargs={"slug": "count-type"})
    response = client_logged.get(url)

    actual = response.content.decode("utf-8")

    assert "66" in actual
    assert f'<a role="button" hx-get="/counts/update/{p.pk}/"' in actual
    assert f'<a role="button" hx-get="/counts/delete/{p.pk}/"' in actual


def test_data_no_records(client_logged):
    CountTypeFactory()

    url = reverse("counts:tab_data", kwargs={"slug": "count-type"})
    response = client_logged.get(url, follow=True)
    actual = response.content.decode("utf-8")

    assert "<b>1999</b> metais įrašų nėra." in actual


# -------------------------------------------------------------------------------------
#                                                                           Tab History
# -------------------------------------------------------------------------------------
def test_history_func():
    view = resolve("/counts/xxx/history/")

    assert views.TabHistory == view.func.view_class


def test_history_200(client_logged):
    obj = CountTypeFactory()
    url = reverse("counts:tab_history", kwargs={"slug": obj.slug})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_history_context(client_logged):
    obj = CountTypeFactory()

    url = reverse("counts:tab_history", kwargs={"slug": obj.slug})
    response = client_logged.get(url)

    assert "chart_weekdays" in response.context
    assert "chart_years" in response.context
    assert "chart_histogram" in response.context
    assert "slug" in response.context
    assert response.context["slug"] == obj.slug


def test_history_chart_weekdays(client_logged):
    obj = CountTypeFactory()
    CountFactory()

    url = reverse("counts:tab_history", kwargs={"slug": obj.slug})
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    assert '<div id="chart-weekdays-container"></div>' in content


def test_history_chart_years(client_logged):
    obj = CountTypeFactory()
    CountFactory()

    url = reverse("counts:tab_history", kwargs={"slug": obj.slug})
    response = client_logged.get(url)

    content = response.content.decode("utf-8")

    assert '<div id="chart-years-container"></div>' in content


# -------------------------------------------------------------------------------------
#                                                               CountType Create/Update
# -------------------------------------------------------------------------------------
def test_count_type_new_func():
    view = resolve("/counts/type/new/")

    assert views.TypeNew is view.func.view_class


def test_count_type_update_func():
    view = resolve("/counts/type/update/1/")

    assert views.TypeUpdate is view.func.view_class


def test_count_type_new_200(client_logged):
    url = reverse("counts:type_new")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_count_type_new_load_form(client_logged):
    url = reverse("counts:type_new")
    response = client_logged.get(url)

    content = response.content.decode("utf-8")
    assert f'hx-post="{url}"' in content


def test_count_type_update_load_form(client_logged):
    obj = CountTypeFactory()

    url = reverse("counts:type_update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert obj.title in content
    assert f'hx-post="{url}"' in content


def test_count_type_new_form(client_logged):
    url = reverse("counts:type_new")
    response = client_logged.get(url)
    form = response.context.get("form")

    assert isinstance(form, forms.CountTypeForm)


def test_count_type_new_form_fields(client_logged):
    url = reverse("counts:type_new")
    response = client_logged.get(url)
    actual = response.content.decode()

    assert actual.count("<input") == 3
    assert actual.count("<button") == 4
    assert 'type="hidden" name="csrfmiddlewaretoken"' in actual
    assert '<input type="text" name="title"' in actual


def test_count_type_new_valid_data(client_logged):
    data = {"title": "XXX"}
    url = reverse("counts:type_new")
    client_logged.post(url, data, follow=True)

    actual = CountType.objects.first()
    assert actual.title == "XXX"


def test_count_type_htmx_status_code(client_logged):
    data = {"title": "XXX"}
    url = reverse("counts:type_new")
    response = client_logged.post(url, data, **{"HTTP_HX-Request": "true"})

    assert response.status_code == 200


def test_count_type_htmx_redirect_header(client_logged):
    data = {"title": "XXX"}
    url = reverse("counts:type_new")
    response = client_logged.post(url, data, **{"HTTP_HX-Request": "true"})

    assert response.headers["HX-Redirect"] == reverse(
        "counts:index", kwargs={"slug": "xxx"}
    )


def test_count_type_new_invalid_data(client_logged):
    data = {"title": "X"}
    url = reverse("counts:type_new")
    response = client_logged.post(url, data)
    form = response.context.get("form")

    assert not form.is_valid()


def test_count_type_update(client_logged):
    obj = CountFactory()

    data = {"title": "YYY"}
    url = reverse("counts:type_update", kwargs={"pk": obj.pk})
    client_logged.post(url, data, follow=True)

    assert CountType.objects.count() == 1
    assert CountType.objects.first().title == "YYY"


def test_count_type_update_htmx_redirect_header(client_logged):
    obj = CountFactory()

    data = {"title": "YYY"}
    url = reverse("counts:type_update", kwargs={"pk": obj.pk})
    response = client_logged.post(url, data, **{"HTTP_HX-Request": "true"})

    assert response.headers["HX-Redirect"] == reverse(
        "counts:index", kwargs={"slug": "yyy"}
    )


def test_count_type_update_not_load_other_user(client_logged, second_user):
    obj = CountTypeFactory(title="xxx", user=second_user)

    url = reverse("counts:type_update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


# -------------------------------------------------------------------------------------
#                                                                      CountType Delete
# -------------------------------------------------------------------------------------
def test_count_types_delete_func():
    view = resolve("/counts/type/delete/1/")

    assert views.TypeDelete is view.func.view_class


def test_count_type_delete_200(client_logged):
    obj = CountTypeFactory()

    url = reverse("counts:type_delete", kwargs={"pk": obj.pk})

    response = client_logged.get(url)

    assert response.status_code == 200


def test_count_type_delete_load_form(client_logged):
    obj = CountTypeFactory()

    url = reverse("counts:type_delete", kwargs={"pk": obj.pk})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert '<form method="POST"' in actual
    assert f'hx-post="{url}"' in actual
    assert "Ar tikrai norite ištrinti: <strong>Count Type</strong>?" in actual


def test_count_type_delete(client_logged):
    _type = CountTypeFactory()
    CountFactory(count_type=_type)

    url = reverse("counts:type_delete", kwargs={"pk": _type.pk})

    client_logged.post(url)

    assert CountType.objects.count() == 0
    assert Count.objects.count() == 0


def test_count_type_delete_htmx_redirect_header(client_logged):
    _type = CountTypeFactory()

    url = reverse("counts:type_delete", kwargs={"pk": _type.pk})
    response = client_logged.post(url, **{"HTTP_HX-Request": "true"})

    assert response.headers["HX-Redirect"] == reverse(
        "counts:index", kwargs={"slug": "count-type"}
    )


def test_count_type_delete_other_user_get_form(client_logged, second_user):
    obj = CountTypeFactory(user=second_user)

    url = reverse("counts:type_delete", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_count_type_delete_other_user_post_form(client_logged, second_user):
    obj = CountTypeFactory(user=second_user)

    url = reverse("counts:type_delete", kwargs={"pk": obj.pk})
    client_logged.post(url)

    assert CountType.objects.all().count() == 1


# -------------------------------------------------------------------------------------
#                                                                          Counts Empty
# -------------------------------------------------------------------------------------
def test_empty_func():
    view = resolve("/counts/none/")

    assert views.Empty is view.func.view_class


def test_empty_200(client_logged):
    url = reverse("counts:empty")
    response = client_logged.get(url)

    assert response.status_code == 200

    actual = response.content.decode("utf-8")
    assert "Jūs neturite skaitiklių." in actual


@pytest.mark.disable_get_user_patch
def test_empty_user_not_logged(client):
    url = reverse("counts:empty")
    response = client.get(url, follow=True)

    assert response.resolver_match.func.view_class is Login


# -------------------------------------------------------------------------------------
#                                                                              Info Row
# -------------------------------------------------------------------------------------
def test_info_row_func():
    view = resolve("/counts/xxx/info_row/")

    assert views.InfoRow is view.func.view_class


@time_machine.travel(datetime(1999, 7, 12))
def test_info_row(client_logged):
    CountFactory(date=date(1999, 7, 8), quantity=1)
    CountFactory(date=date(1999, 1, 1), quantity=1)
    CountFactory(date=date(1999, 1, 1), quantity=1)

    url = reverse("counts:index", kwargs={"slug": "count-type"})
    response = client_logged.get(url)
    context = response.context

    assert context["object"].title == "Count Type"
    assert context["week"] == 28
    assert context["total"] == 3
    assert round(context["ratio"], 2) == 0.11
    assert context["current_gap"] == 4


@time_machine.travel(datetime(2026, 7, 12))
def test_info_row_week_of_a_finished_year_is_its_real_iso_count(
    client_logged, main_user
):
    # 2025 has 52 ISO weeks; it is not a leap year but starts on a Wednesday,
    # which an older rule read as 53 — and a per-week average divided by it
    main_user.year = 2025
    main_user.save()

    CountFactory(date=date(2025, 7, 8), quantity=52)

    url = reverse("counts:index", kwargs={"slug": "count-type"})
    response = client_logged.get(url)

    assert response.context["week"] == 52
    assert response.context["ratio"] == 1.0


@time_machine.travel(datetime(2000, 7, 12))
def test_info_row_gap_in_past_view(client_logged, main_user):
    main_user.year = 1999

    CountFactory(date=date(1999, 1, 1), quantity=1)
    CountFactory(date=date(2000, 1, 1), quantity=1)

    url = reverse("counts:index", kwargs={"slug": "count-type"})
    response = client_logged.get(url)
    context = response.context

    assert context["current_gap"] == 0
