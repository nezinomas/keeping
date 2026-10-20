import json
import re
from datetime import date
from unittest.mock import patch

import pytest
import time_machine
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from ...accounts.tests.factories import AccountFactory
from ...core.lib.utils import get_action_buttons_html
from ...core.tests.utils import change_profile_year, clean_content, view_for
from ...users.views import Login
from .. import models
from ..forms import ExpenseNameChoicesMixin
from ..forms_import import ReviewLineForm
from ..views import expenses as expense_views
from ..views import expenses_import
from ..views.expenses import Lists, LoadExpenseName
from .factories import ExpenseFactory, ExpenseNameFactory, ExpenseTypeFactory

pytestmark = pytest.mark.django_db


@pytest.fixture()
def type_with_two_names():
    expense_type = ExpenseTypeFactory()
    ExpenseNameFactory(title="F", parent=expense_type)
    ExpenseNameFactory(title="S", parent=expense_type, valid_for=1999)
    return expense_type


def _active_tab(name):
    return rf'id="tab-{name}"\s+class="tab active"'


def _listed_month(month):
    # the month buttons draw every month's url too; only #data loads one
    return rf'id="data"[^>]*hx-get="/expenses/list/{month}/"'


@pytest.mark.parametrize(
    "url_name, kwargs, expected",
    [
        pytest.param("expenses:index", {}, [_active_tab("index")], id="overview"),
        pytest.param(
            "expenses:tab_data",
            {},
            [_active_tab("data"), _listed_month(2)],
            id="data_this_month",
        ),
        pytest.param(
            "expenses:index",
            {"month": 3},
            [_active_tab("data"), _listed_month(3)],
            id="nav_month",
        ),
    ],
)
@time_machine.travel("1999-02-08")
def test_the_page_opens_the_tab_and_month_its_url_names(
    client_logged, url_name, kwargs, expected
):
    content = client_logged.get(reverse(url_name, kwargs=kwargs)).content.decode()

    for pattern in expected:
        assert re.search(pattern, content)


def test_a_tab_url_visited_plainly_returns_the_whole_page(client_logged):
    content = client_logged.get(reverse("expenses:tab_index")).content.decode()

    assert 'role="tablist"' in content
    assert content.count('class="quick-add__pill"') == 2
    assert 'class="quick-add__pill" href="/expenses/import/">Importuoti čekį' in content
    assert 'class="quick-add__pill" hx-get="/expenses/new/"' in content
    assert "Pridėti išlaidas" in content


def test_a_tab_url_requested_by_htmx_returns_the_fragment_alone(client_logged):
    content = client_logged.get(
        reverse("expenses:tab_index"), headers={"HX-Request": "true"}
    ).content.decode()

    assert "<title>Išlaidos | Apžvalga</title>" in content
    assert 'role="tablist"' not in content
    assert "quick-add" not in content


def _tab_queries(client, url_name):
    with CaptureQueriesContext(connection) as queries:
        client.get(reverse(url_name), headers={"HX-Request": "true"})
    return len(queries)


@pytest.mark.parametrize("url_name", ["expenses:tab_index", "expenses:tab_data"])
def test_tab_query_count_does_not_grow_with_the_expenses(client_logged, url_name):
    for i in range(2):
        ExpenseFactory(expense_type=ExpenseTypeFactory(title=f"T{i}"))
    two = _tab_queries(client_logged, url_name)

    for i in range(2, 6):
        ExpenseFactory(expense_type=ExpenseTypeFactory(title=f"T{i}"))
    six = _tab_queries(client_logged, url_name)

    assert six == two


@time_machine.travel("1999-09-15")
def test_overview_states_a_running_year_to_its_boundary(client_logged):
    food = ExpenseTypeFactory(title="Maistas")
    ExpenseFactory(date=date(1999, 2, 5), price=90_000, expense_type=food)
    ExpenseFactory(date=date(1999, 11, 5), price=60_000, expense_type=food)
    ExpenseFactory(date=date(1998, 1, 5), price=80_000, expense_type=food)
    ExpenseFactory(date=date(1998, 12, 5), price=5_000, expense_type=food)

    content = client_logged.get(reverse("expenses:tab_index")).content.decode()

    assert ">900</span>" in content
    assert "Pernai 800<" in content
    assert ">100</span>" in content
    assert "9 mėnesiai" in content
    assert ">Maistas</span>" in content
    assert "100% metų sumos" in content
    assert "Didžiausią šių metų dalį sudaranti išlaidų rūšis" in content


def test_overview_of_a_past_year_reads_the_whole_year(client_logged):
    ExpenseFactory(date=date(1999, 3, 5), price=60_000)
    ExpenseFactory(date=date(1998, 12, 5), price=5_000)

    content = client_logged.get(reverse("expenses:tab_index")).content.decode()

    assert ">600</span>" in content
    assert "Pernai 50<" in content
    assert ">50</span>" in content


def test_overview_of_an_empty_year_is_three_empty_cards(client_logged):
    ExpenseFactory(date=date(1998, 3, 5))

    content = client_logged.get(reverse("expenses:tab_index")).content.decode()

    assert content.count("trend-card__value--empty") == 3


@time_machine.travel("1999-09-15")
def test_overview_charts_the_year_against_last_year_to_the_same_day(client_logged):
    ExpenseFactory(date=date(1999, 2, 5), price=90_000)
    ExpenseFactory(date=date(1998, 9, 10), price=80_000)
    ExpenseFactory(date=date(1998, 9, 20), price=5_000)

    content = client_logged.get(reverse("expenses:tab_index")).content.decode()
    chart = json.loads(
        re.search(r'id="chart-months-data"[^>]*>(.*?)</script>', content)[1]
    )
    data = {series["name"]: series["data"] for series in chart["series"]}

    assert data["1999"] == [0.0, 900.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    assert data["1998"][8] == 800.0
    assert "Išlaidos per mėnesį" in content


@pytest.mark.parametrize(
    "url_name, lit",
    [
        pytest.param("expenses:tab_data", True, id="expenses_tab"),
        pytest.param("plans:tab_expenses", False, id="plans"),
        pytest.param("bookkeeping:detailed_expenses", False, id="detailed"),
        pytest.param("bookkeeping:summary_expenses", False, id="summary"),
    ],
)
def test_the_navbar_lights_expenses_only_on_its_own_pages(client_logged, url_name, lit):
    content = client_logged.get(reverse(url_name)).content.decode()

    assert bool(re.search(r'class="active">\s*<a href="/expenses/"', content)) is lit


@pytest.mark.parametrize(
    "today, dates, kwargs, expected",
    [
        pytest.param(
            "1999-02-08",
            [date(1999, 1, 1), date(1999, 2, 7)],
            {},
            [date(1999, 2, 7)],
            id="no_month_is_this_month",
        ),
        pytest.param(
            "1999-02-08",
            [date(1999, 1, 1), date(1999, 2, 7)],
            {"month": 1},
            [date(1999, 1, 1)],
            id="month_kwarg",
        ),
        pytest.param(
            "1999-01-01",
            [date(1998, 1, 1), date(1999, 1, 1), date(1999, 2, 1)],
            {},
            [date(1999, 1, 1)],
            id="no_month_in_user_year",
        ),
        pytest.param(
            "1999-02-01",
            [date(1998, 1, 1), date(1999, 1, 1), date(1999, 2, 1)],
            {"month": 1},
            [date(1999, 1, 1)],
            id="january",
        ),
        pytest.param(
            "1999-01-01",
            [date(1998, 1, 1), date(1999, 1, 1), date(1999, 2, 1)],
            {"month": 13},
            [date(1999, 1, 1), date(1999, 2, 1)],
            id="all_year",
        ),
        pytest.param(
            "1999-01-01",
            [date(1998, 1, 1), date(1999, 1, 1), date(1999, 2, 1)],
            {"month": 133},
            [date(1999, 1, 1), date(1999, 2, 1)],
            id="any_number_is_all_year",
        ),
    ],
)
def test_expenses_list_filters_by_month(client_logged, today, dates, kwargs, expected):
    for expense_date in dates:
        ExpenseFactory(date=expense_date)

    url = reverse("expenses:list", kwargs=kwargs)
    with time_machine.travel(today):
        actual = client_logged.get(url).context["object_list"]

    assert sorted(row["date"] for row in actual) == expected


@pytest.mark.parametrize(
    "month, expected",
    [
        pytest.param(1, "<b>1</b> mėnesį įrašų nėra", id="month"),
        pytest.param(12, "<b>12</b> mėnesį įrašų nėra", id="december"),
        pytest.param(13, "<b>1999</b> metais įrašų nėra", id="all_year"),
        pytest.param(14, "<b>1999</b> metais įrašų nėra", id="above_all_year"),
    ],
)
def test_expenses_list_empty_notice(client_logged, month, expected):
    url = reverse("expenses:list", kwargs={"month": month})
    actual = client_logged.get(url).content.decode("utf-8")

    assert expected in actual


def test_lists_renders_row_buttons_equal_for_2_and_6_expenses(client_logged):
    url = reverse("expenses:list", kwargs={"month": 1})
    buttons = {"cotton/td_edit.html", "cotton/td_delete.html"}
    # the buttons render once per process (lru_cache): warm it, or the first
    # request alone renders them
    get_action_buttons_html()

    def button_renders():
        templates = client_logged.get(url).templates
        return sorted(t.name for t in templates if t.name in buttons)

    ExpenseFactory.create_batch(2)
    two = button_renders()
    ExpenseFactory.create_batch(4)
    six = button_renders()

    assert two == six


def test_expenses_lists_302(client):
    url = reverse("expenses:list")
    response = client.get(url)

    assert response.status_code == 302


@time_machine.travel("1974-08-08")
def test_expenses_load_new_form(main_user, client_logged):
    main_user.year = 3000
    main_user.save()

    url = reverse("expenses:new")

    response = client_logged.get(url)
    actual = clean_content(response.content.decode("utf-8"))

    assert f'hx-post="{url}"' in actual
    assert "3000-08-08" in actual
    assert "Įrašyti</button>" in actual
    assert "Įrašyti ir uždaryti</button>" in actual


def test_expenses_new_form_file_control_speaks_the_app_language(client_logged):
    url = reverse("expenses:new")

    text = client_logged.get(url).content.decode()

    assert "Pasirinkti failą" in text
    assert 'data-empty="Failas nepasirinktas"' in text


def test_expenses_save(client_logged):
    account = AccountFactory()
    expense_type = ExpenseTypeFactory()
    expense_name = ExpenseNameFactory()

    data = {
        "date": "1999-01-01",
        "price": 0.01,
        "quantity": 33,
        "account": account.pk,
        "expense_type": expense_type.pk,
        "expense_name": expense_name.pk,
    }

    url = reverse("expenses:new")
    client_logged.post(url, data, follow=True)

    actual = models.Expense.objects.last()
    assert actual.date == date(1999, 1, 1)
    assert actual.price == 1
    assert actual.quantity == 33
    assert actual.account.title == "Account1"
    assert actual.expense_type.title == "Expense Type"
    assert actual.expense_name.title == "Expense Name"


def test_expenses_save_invalid_data(client_logged):
    data = {
        "date": "x",
        "price": "x",
        "quantity": 0,
        "account": "x",
        "expense_type": "x",
    }

    url = reverse("expenses:new")
    response = client_logged.post(url, data)
    actual = response.context["form"]

    assert not actual.is_valid()


def test_expenses_load_update_form(client_logged):
    expense = ExpenseFactory()

    url = reverse("expenses:update", kwargs={"pk": expense.pk})
    response = client_logged.get(url)
    actual = clean_content(response.content.decode("utf-8"))

    assert f'hx-post="{url}"' in actual
    assert "Atnaujinti ir uždaryti</button>" in actual


def test_expenses_load_update_form_field_values(client_logged):
    expense = ExpenseFactory(price=1)

    url = reverse("expenses:update", kwargs={"pk": expense.pk})
    response = client_logged.get(url)
    instance = response.context["form"].instance
    form = response.context["form"].as_p()

    assert instance.date == date(1999, 1, 1)
    assert instance.price == 0.01
    assert instance.quantity == 13
    assert instance.expense_type.title == "Expense Type"
    assert instance.expense_name.title == "Expense Name"
    assert instance.remark == "Remark"
    assert '<input type="text" name="date" value="1999-01-01"' in form
    assert f'<option value="{expense.account.pk}" selected>Account1</option>' in form
    assert (
        f'<option value="{expense.expense_type.pk}" selected>Expense Type</option>'
        in form
    )
    assert (
        f'<option value="{expense.expense_name.pk}" selected>Expense Name</option>'
        in form
    )
    assert '<input type="number" name="quantity" value="13"' in form
    assert '<input type="text" name="price" value="0.01"' in form


def test_expenses_update_to_another_year(client_logged):
    expense = ExpenseFactory()

    data = {
        "price": "150",
        "quantity": 13,
        "date": "2010-12-31",
        "remark": "Pastaba",
        "account": expense.account.pk,
        "expense_type": expense.expense_type.pk,
        "expense_name": expense.expense_name.pk,
    }
    url = reverse("expenses:update", kwargs={"pk": expense.pk})

    client_logged.post(url, data)

    actual = models.Expense.objects.get(pk=expense.pk)
    assert actual.date == date(2010, 12, 31)
    assert actual.quantity == 13


@pytest.mark.parametrize(
    "created, price, posted_date, expected_price",
    [
        pytest.param({}, 150, "1999-12-31", 15_000, id="saves_posted_values"),
        pytest.param(
            {"date": date(2000, 3, 3), "price": 477},
            4.89,
            "2000-03-04",
            489,
            id="float_price_is_whole_cents",
        ),
        pytest.param(
            {"date": date(1974, 12, 12)},
            0.01,
            "1998-12-12",
            1,
            id="past_record",
        ),
    ],
)
@time_machine.travel("2000-03-03")
def test_expenses_update(client_logged, created, price, posted_date, expected_price):
    expense = ExpenseFactory(**created)

    data = {
        "price": price,
        "quantity": 33,
        "date": posted_date,
        "remark": "Pastaba",
        "account": expense.account.pk,
        "expense_type": expense.expense_type.pk,
        "expense_name": expense.expense_name.pk,
    }
    url = reverse("expenses:update", kwargs={"pk": expense.pk})

    client_logged.post(url, data)

    actual = models.Expense.objects.get(pk=expense.pk)
    assert actual.date == date.fromisoformat(posted_date)
    assert actual.price == expected_price
    assert actual.quantity == 33
    assert actual.account.title == "Account1"
    assert actual.expense_type.title == "Expense Type"
    assert actual.expense_name.title == "Expense Name"
    assert actual.remark == "Pastaba"


@time_machine.travel("2000-03-03")
def test_expenses_update_type_and_name(client_logged):
    expense = ExpenseFactory()
    new_type = ExpenseTypeFactory(title="XXX")
    new_name = ExpenseNameFactory(title="YYY", parent=new_type)

    data = {
        "price": 150,
        "quantity": 33,
        "date": "1999-12-31",
        "remark": "Pastaba",
        "account": expense.account.pk,
        "expense_type": new_type.pk,
        "expense_name": new_name.pk,
    }
    url = reverse("expenses:update", kwargs={"pk": expense.pk})

    client_logged.post(url, data)

    actual = models.Expense.objects.get(pk=expense.pk)
    assert actual.date == date(1999, 12, 31)
    assert actual.price == 15_000
    assert actual.quantity == 33
    assert actual.account.title == "Account1"
    assert actual.expense_type.title == "XXX"
    assert actual.expense_name.title == "YYY"
    assert actual.remark == "Pastaba"


def test_expenses_update_price_for_closed_account(client_logged):
    account = AccountFactory(title="XXX", closed=2000)
    expense = ExpenseFactory(account=account, date=date(1999, 1, 1))

    data = {
        "price": 150,
        "quantity": 33,
        "date": expense.date,
        "remark": "Pastaba",
        "account": account.pk,
        "expense_type": expense.expense_type.pk,
        "expense_name": expense.expense_name.pk,
    }
    url = reverse("expenses:update", kwargs={"pk": expense.pk})

    client_logged.post(url, data)

    actual = models.Expense.objects.get(pk=expense.pk)
    assert actual.date == expense.date
    assert actual.price == 15_000
    assert actual.quantity == 33
    assert actual.account.title == account.title
    assert actual.expense_type.title == expense.expense_type.title
    assert actual.expense_name.title == expense.expense_name.title
    assert actual.remark == "Pastaba"


def test_expenses_update_with_closed_account_date_greater_than_closed_value(
    client_logged,
):
    account = AccountFactory(title="XXX", closed=2000)
    expense = ExpenseFactory(account=account, date=date(1999, 1, 1))

    data = {
        "price": 150,
        "quantity": 33,
        "date": "2023-1-1",
        "remark": "Pastaba",
        "account": account.pk,
        "expense_type": expense.expense_type.pk,
        "expense_name": expense.expense_name.pk,
    }
    url = reverse("expenses:update", kwargs={"pk": expense.pk})

    response = client_logged.post(url, data)
    form = response.context["form"]

    assert len(form.errors) == 1
    assert (
        "Data negali būti vėlesnė nei sąskaitos uždarymo data. Sąskaita buvo uždaryta 2000."  # noqa: E501
        in form.errors["date"]
    )


def test_expenses_not_load_other_journal(client_logged, second_user):
    own_account = AccountFactory(title="a1")
    other_account = AccountFactory(journal=second_user.journal, title="a2")
    own_type = ExpenseTypeFactory(title="xxx")
    other_type = ExpenseTypeFactory(title="yyy", journal=second_user.journal)

    ExpenseFactory(expense_type=own_type, account=own_account)
    other_expense = ExpenseFactory(
        expense_type=other_type, account=other_account, price=666
    )

    url = reverse("expenses:update", kwargs={"pk": other_expense.pk})
    response = client_logged.get(url)

    form = response.content.decode("utf-8")

    assert other_type.title not in form
    assert str(other_expense.price) not in form


def test_expenses_data_search_form(client_logged):
    url = reverse("expenses:tab_data")
    response = client_logged.get(url).content.decode("utf-8")

    assert '<input type="search" name="search"' in response
    assert reverse("expenses:search") in response


@pytest.mark.parametrize(
    "price, expected",
    [
        pytest.param(7777, "77,77", id="converted"),
        pytest.param(100_000, "1.000,00", id="with_thousands"),
    ],
)
@time_machine.travel("1999-1-1")
def test_expenses_list_price_converted(client_logged, price, expected):
    ExpenseFactory(price=price)

    url = reverse("expenses:list", kwargs={"month": 1})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert expected in actual


def test_view_expenses_delete_load_form(client_logged):
    expense = ExpenseFactory()

    url = reverse("expenses:delete", kwargs={"pk": expense.pk})
    response = client_logged.get(url)

    actual = response.content.decode("utf-8")

    assert f'hx-post="{url}"' in actual
    assert '<form method="POST"' in actual
    assert (
        "Ar tikrai norite ištrinti: <strong>1999-01-01/Expense Type/Expense Name</strong>?"  # noqa: E501
        in actual
    )


def test_view_expenses_delete(client_logged):
    expense = ExpenseFactory()

    assert models.Expense.objects.all().count() == 1
    url = reverse("expenses:delete", kwargs={"pk": expense.pk})

    client_logged.post(url)

    assert models.Expense.objects.all().count() == 0


def test_expenses_delete_other_journal_get_form(client_logged, second_user):
    other_type = ExpenseTypeFactory(title="yyy", journal=second_user.journal)
    other_expense = ExpenseFactory(
        expense_type=other_type,
        account=AccountFactory(title="A2", journal=second_user.journal),
        price=666,
    )

    url = reverse("expenses:delete", kwargs={"pk": other_expense.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_expenses_delete_other_journal_post_form(client_logged, second_user):
    other_type = ExpenseTypeFactory(title="yyy", journal=second_user.journal)
    other_expense = ExpenseFactory(
        expense_type=other_type,
        account=AccountFactory(title="A2", journal=second_user.journal),
        price=666,
    )

    url = reverse("expenses:delete", kwargs={"pk": other_expense.pk})
    client_logged.post(url)

    assert models.Expense.objects.all().count() == 1


def test_expense_type_not_load_other_journal(client_logged, second_user):
    ExpenseTypeFactory(title="xxx")
    other_type = ExpenseTypeFactory(title="yyy", journal=second_user.journal)

    url = reverse("expenses:type_update", kwargs={"pk": other_type.pk})
    response = client_logged.get(url)

    form = response.content.decode("utf-8")

    assert other_type.title not in form


@pytest.mark.parametrize(
    "url_name",
    [
        pytest.param("expenses:type_new", id="type_new"),
        pytest.param("expenses:name_new", id="name_new"),
    ],
)
def test_expense_new_form_posts_to_its_url(client_logged, url_name):
    url = reverse(url_name)
    actual = client_logged.get(url).content.decode("utf-8")

    assert f'hx-post="{url}"' in actual


def test_expense_type_update_form_posts_to_its_url(client_logged):
    expense_type = ExpenseTypeFactory()

    url = reverse("expenses:type_update", kwargs={"pk": expense_type.pk})
    actual = client_logged.get(url).content.decode("utf-8")

    assert f'hx-post="{url}"' in actual


def test_expense_name_save_data(client_logged):
    url = reverse("expenses:name_new")
    expense_type = ExpenseTypeFactory()

    data = {"title": "TTT", "parent": expense_type.pk}

    response = client_logged.post(url, data, follow=True)

    actual = response.content.decode("utf-8")

    assert "TTT" in actual


def test_expense_name_save_invalid_data(client_logged):
    data = {"title": "x", "parent": 0}

    url = reverse("expenses:name_new")

    response = client_logged.post(url, data)

    actual = response.context["form"]

    assert not actual.is_valid()


def test_expense_name_load_for_form_for_update(client_logged):
    expense_name = ExpenseNameFactory(title="XXX")

    url = reverse("expenses:name_update", kwargs={"pk": expense_name.pk})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert f'hx-post="{url}"' in actual
    assert '<input type="text" name="title" value="XXX"' in actual


def test_expense_name_update(client_logged):
    expense_name = ExpenseNameFactory()

    data = {"title": "TTT", "valid_for": 2000, "parent": expense_name.parent.pk}
    url = reverse("expenses:name_update", kwargs={"pk": expense_name.pk})

    response = client_logged.post(url, data, follow=True)

    actual = response.content.decode("utf-8")

    assert "TTT" in actual


def test_expense_name_not_load_other_journal(client_logged, second_user):
    own_type = ExpenseTypeFactory(title="xxx")
    other_type = ExpenseTypeFactory(title="yyy", journal=second_user.journal)

    ExpenseNameFactory(parent=own_type)
    other_name = ExpenseNameFactory(parent=other_type)

    url = reverse("expenses:name_update", kwargs={"pk": other_name.pk})
    response = client_logged.get(url)

    actual = response.content.decode("utf-8")

    assert other_name.title not in actual
    assert other_type.title not in actual


def test_load_expense_name_isnull_count(client_logged, type_with_two_names):
    change_profile_year(client_logged)

    url = reverse("expenses:load_expense_name")
    response = client_logged.get(url, {"expense_type": type_with_two_names.pk})

    assert response.context["object_list"].count() == 1


def test_load_expense_name_all(client_logged, type_with_two_names):
    url = reverse("expenses:load_expense_name")
    response = client_logged.get(url, {"expense_type": type_with_two_names.pk})

    assert response.context["object_list"].count() == 2


@pytest.mark.usefixtures("type_with_two_names")
@pytest.mark.parametrize(
    "expense_type",
    [
        pytest.param("", id="empty_parent"),
        pytest.param("abc", id="type_not_integer"),
    ],
)
def test_load_expense_name_without_a_type_is_missing(client_logged, expense_type):
    url = reverse("expenses:load_expense_name")
    response = client_logged.get(url, {"expense_type": expense_type})

    assert response.context["object_list"] == []


def test_load_expense_name_must_logged(client):
    url = reverse("expenses:load_expense_name")

    response = client.get(url, follow=True)

    assert response.status_code == 200
    assert response.resolver_match.func.view_class is Login


@pytest.mark.parametrize(
    "names, type_field, params, expected",
    [
        pytest.param(
            [{"title": "N"}],
            "form-3-expense_type",
            {"prefix": "form-3"},
            ["N"],
            id="prefix",
        ),
        pytest.param(
            [{"title": "N"}],
            "expense_type",
            {"prefix": "form-3"},
            [],
            id="prefix_reads_only_prefixed_field",
        ),
        pytest.param(
            [{"title": "N-default"}, {"title": "N-2005", "valid_for": 2005}],
            "expense_type",
            {"year": 2005},
            ["N-2005", "N-default"],
            id="year",
        ),
        pytest.param(
            [{"title": "N-2005", "valid_for": 2005}],
            "expense_type",
            {"year": 2006},
            [],
            id="year_excludes_other_year",
        ),
        pytest.param(
            [{"title": "N", "valid_for": 2005}],
            "form-3-expense_type",
            {"prefix": "form-3", "year": 2005},
            ["N"],
            id="prefix_and_year",
        ),
        pytest.param(
            [{"title": "N"}],
            "expense_type",
            {"year": "abc"},
            ["N"],
            id="year_not_integer_falls_back_to_user_year",
        ),
    ],
)
def test_load_expense_name_reads_prefix_and_year(
    client_logged, names, type_field, params, expected
):
    expense_type = ExpenseTypeFactory()
    for name in names:
        ExpenseNameFactory(parent=expense_type, **name)

    url = reverse("expenses:load_expense_name")
    response = client_logged.get(url, {type_field: expense_type.pk} | params)

    actual = sorted(name.title for name in response.context["object_list"])
    assert actual == expected


def test_load_expense_name_other_journal_type_yields_no_names(
    client_logged, second_user
):
    other_type = ExpenseTypeFactory(journal=second_user.journal)
    ExpenseNameFactory(title="N", parent=other_type)

    url = reverse("expenses:load_expense_name")
    response = client_logged.get(url, {"expense_type": other_type.pk})

    assert response.context["object_list"].count() == 0


@pytest.mark.parametrize(
    "query",
    [
        pytest.param({"search": "xxx"}, id="no_match"),
        pytest.param({}, id="no_search_given"),
    ],
)
def test_search_not_found(client_logged, query):
    ExpenseFactory()

    url = reverse("expenses:search")
    response = client_logged.get(url, query)
    actual = response.content.decode("utf-8")

    assert "Nieko nerasta" in actual


def test_search_found(client_logged):
    ExpenseFactory()

    url = reverse("expenses:search")
    response = client_logged.get(url, {"search": "type"})
    actual = response.content.decode("utf-8")

    assert "1999-01-01" in actual
    assert "Remark" in actual


@pytest.mark.parametrize(
    "query, expected",
    [
        pytest.param({"search": "type"}, 50, id="first_page"),
        pytest.param({"page": 2, "search": "type"}, 1, id="second_page"),
    ],
)
def test_search_pagination(client_logged, query, expected):
    account = AccountFactory()
    expense_type = ExpenseTypeFactory()
    expense_name = ExpenseNameFactory()
    expenses = ExpenseFactory.build_batch(
        51, account=account, expense_type=expense_type, expense_name=expense_name
    )
    models.Expense.objects.bulk_create(expenses)

    url = reverse("expenses:search")
    response = client_logged.get(url, query)
    actual = response.context["object_list"]

    assert len(actual) == expected


def test_search_statistic(client_logged):
    ExpenseFactory(price=100)
    ExpenseFactory(price=200, quantity=2, remark="xxx")
    ExpenseFactory(price=300, quantity=3, remark="xxx")

    url = reverse("expenses:search")
    response = client_logged.get(url, {"page": 2, "search": "xxx"})

    assert response.context["sum_price"] == 500
    assert response.context["sum_quantity"] == 5
    assert response.context["average"] == 100


def test_search_statistic_not_found(client_logged):
    ExpenseFactory(price=100)
    ExpenseFactory(price=200, quantity=2)
    ExpenseFactory(price=300, quantity=3)

    url = reverse("expenses:search")
    response = client_logged.get(url, {"page": 2, "search": "xxx"})
    actual = response.content.decode("utf-8")

    assert "Nieko nerasta" in actual
    assert "search-statistic" not in actual


def _get(view):
    return view.get(view.request)


def _import_save(rf, user):
    request = rf.post("/")
    request.user = user

    # the receipt form's account read raises first
    with patch.object(expenses_import, "ReviewReceiptForm"):
        return expenses_import.ImportSave().post(request)


class _Names(ExpenseNameChoicesMixin):
    def __init__(self, user):
        self.user = user


@pytest.mark.parametrize(
    "call",
    [
        pytest.param(
            lambda rf, u: view_for(rf, u, expense_views.TabIndex).get_context_data(),
            id="tab_index",
        ),
        pytest.param(lambda rf, u: view_for(rf, u, Lists).get_queryset(), id="list"),
        pytest.param(
            lambda rf, u: _get(view_for(rf, u, LoadExpenseName, "/?expense_type=1")),
            id="load_expense_name",
        ),
        pytest.param(lambda rf, u: _Names(u).names_year(), id="names_year"),
        pytest.param(lambda rf, u: _import_save(rf, u), id="import_save"),
        pytest.param(
            lambda rf, u: ReviewLineForm(user=u, year=1999), id="review_line_form"
        ),
    ],
)
def test_a_user_with_no_year_raises(rf, main_user, call):
    main_user.year = None

    with pytest.raises(ValueError, match="has no year"):
        call(rf, main_user)
