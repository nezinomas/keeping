from datetime import date

import pytest
import time_machine
from django.urls import resolve, reverse

from ...accounts.factories import AccountFactory
from ...core.tests.utils import change_profile_year, clean_content
from .. import models
from ..factories import Expense, ExpenseFactory, ExpenseNameFactory, ExpenseTypeFactory
from ..views import expenses, expenses_name, expenses_type

pytestmark = pytest.mark.django_db


@pytest.fixture()
def _db_data():
    ExpenseTypeFactory.reset_sequence()
    ExpenseNameFactory(title="F")
    ExpenseNameFactory(title="S", valid_for=1999)


# -------------------------------------------------------------------------------------
#                                                                               Expense
# -------------------------------------------------------------------------------------
def test_expenses_index_func():
    view = resolve("/expenses/")

    assert expenses.Index == view.func.view_class


def test_expenses_index_alternative_func():
    view = resolve("/expenses/5/")

    assert expenses.Index == view.func.view_class


def test_expenses_index_200(client_logged):
    url = reverse("expenses:index")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_expenses_index_alternative_200(client_logged):
    url = reverse("expenses:index", kwargs={"month": 1})
    response = client_logged.get(url)

    assert response.status_code == 200


@time_machine.travel("1999-02-08")
def test_expenses_index_context(client_logged):
    ExpenseFactory(date=date(1999, 1, 1))
    ExpenseFactory(date=date(1999, 2, 7))

    url = reverse("expenses:index")
    actual = client_logged.get(url).context["month"]

    assert actual == 2


@time_machine.travel("1999-02-08")
def test_expenses_index_alternative_context(client_logged):
    ExpenseFactory(date=date(1999, 1, 1))
    ExpenseFactory(date=date(1999, 2, 7))

    url = reverse("expenses:index", kwargs={"month": 2})
    actual = client_logged.get(url).context["month"]

    assert actual == 2


def test_expenses_lists_func():
    view = resolve("/expenses/list/")

    assert expenses.Lists == view.func.view_class


def test_expenses_lists_alternative_func():
    view = resolve("/expenses/list/1/")

    assert expenses.Lists == view.func.view_class


def test_expenses_lists_200(client_logged):
    url = reverse("expenses:list")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_expenses_lists_alternative_200(client_logged):
    url = reverse("expenses:list", kwargs={"month": 1})
    response = client_logged.get(url)

    assert response.status_code == 200


@time_machine.travel("1999-02-08")
def test_expenses_lists_context(client_logged):
    ExpenseFactory(date=date(1999, 1, 1))
    ExpenseFactory(date=date(1999, 2, 7))

    url = reverse("expenses:list")
    actual = client_logged.get(url).context["object_list"]

    assert len(actual) == 1
    assert actual[0]["date"] == date(1999, 2, 7)


@time_machine.travel("1999-02-08")
def test_expenses_lists_alternative_context(client_logged):
    ExpenseFactory(date=date(1999, 1, 1))
    ExpenseFactory(date=date(1999, 2, 7))

    url = reverse("expenses:list", kwargs={"month": 2})
    actual = client_logged.get(url).context["object_list"]

    assert len(actual) == 1
    assert actual[0]["date"] == date(1999, 2, 7)


def test_expenses_lists_302(client):
    url = reverse("expenses:list")
    response = client.get(url)

    assert response.status_code == 302


def test_expenses_new_func():
    view = resolve("/expenses/new/")

    assert expenses.New == view.func.view_class


def test_expenses_update_func():
    view = resolve("/expenses/update/1/")

    assert expenses.Update == view.func.view_class


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


def test_expenses_save(client_logged):
    a = AccountFactory()
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory()

    data = {
        "date": "1999-01-01",
        "price": 0.01,
        "quantity": 33,
        "account": a.pk,
        "expense_type": t.pk,
        "expense_name": n.pk,
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
    e = ExpenseFactory()

    url = reverse("expenses:update", kwargs={"pk": e.pk})
    response = client_logged.get(url)
    actual = clean_content(response.content.decode("utf-8"))

    assert f'hx-post="{url}"' in actual
    assert "Atnaujinti ir uždaryti</button>" in actual


def test_expenses_load_update_form_instance_field_values(client_logged):
    e = ExpenseFactory(price=1)

    url = reverse("expenses:update", kwargs={"pk": e.pk})
    response = client_logged.get(url)
    form = response.context["form"]

    assert form.instance.date == date(1999, 1, 1)
    assert form.instance.price == 0.01
    assert form.instance.quantity == 13
    assert form.instance.expense_type.title == "Expense Type"
    assert form.instance.expense_name.title == "Expense Name"
    assert form.instance.remark == "Remark"


def test_expenses_load_update_form_field_values(client_logged):
    e = ExpenseFactory(price=1)

    url = reverse("expenses:update", kwargs={"pk": e.pk})
    response = client_logged.get(url)
    form = response.context["form"].as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form
    assert '<option value="1" selected>Account1</option>' in form
    assert '<option value="1" selected>Expense Type</option>' in form
    assert '<option value="1" selected>Expense Name</option>' in form
    assert '<input type="number" name="quantity" value="13"' in form
    assert '<input type="number" name="price" value="0.01"' in form


def test_expenses_update_to_another_year(client_logged):
    e = ExpenseFactory()

    data = {
        "price": "150",
        "quantity": 13,
        "date": "2010-12-31",
        "remark": "Pastaba",
        "account": 1,
        "expense_type": 1,
        "expense_name": 1,
    }
    url = reverse("expenses:update", kwargs={"pk": e.pk})

    client_logged.post(url, data)

    actual = models.Expense.objects.get(pk=e.pk)
    assert actual.date == date(2010, 12, 31)
    assert actual.quantity == 13


def test_expenses_update(client_logged):
    e = ExpenseFactory()

    data = {
        "price": 150,
        "quantity": 33,
        "date": "1999-12-31",
        "remark": "Pastaba",
        "account": 1,
        "expense_type": e.expense_type.pk,
        "expense_name": e.expense_name.pk,
    }
    url = reverse("expenses:update", kwargs={"pk": e.pk})

    client_logged.post(url, data)

    actual = models.Expense.objects.get(pk=e.pk)
    assert actual.date == date(1999, 12, 31)
    assert actual.price == 15_000
    assert actual.quantity == 33
    assert actual.account.title == "Account1"
    assert actual.expense_type.title == "Expense Type"
    assert actual.expense_name.title == "Expense Name"
    assert actual.remark == "Pastaba"


def test_expenses_update_price_for_closed_account(client_logged, main_user):
    main_user.year = 2023

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


def test_expenses_update_with_closed_account_date_greated_than_closed_value(
    client_logged, main_user
):
    main_user.year = 2023

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


def test_expenses_update_price_with_489(client_logged):
    e = ExpenseFactory(date=date.today(), price=477)

    data = {
        "price": 4.89,
        "quantity": 33,
        "date": "2000-03-04",
        "remark": "Pastaba",
        "account": 1,
        "expense_type": e.expense_type.pk,
        "expense_name": e.expense_name.pk,
    }
    url = reverse("expenses:update", kwargs={"pk": e.pk})

    client_logged.post(url, data, follow=True)

    actual = models.Expense.objects.get(pk=e.pk)
    assert actual.date == date(2000, 3, 4)
    assert actual.price == 489
    assert actual.quantity == 33
    assert actual.account.title == "Account1"
    assert actual.expense_type.title == "Expense Type"
    assert actual.expense_name.title == "Expense Name"
    assert actual.remark == "Pastaba"


def test_expenses_update_type_and_name(client_logged):
    e = ExpenseFactory()
    t = ExpenseTypeFactory(title="XXX")
    n = ExpenseNameFactory(title="YYY", parent=t)

    data = {
        "price": 150,
        "quantity": 33,
        "date": "1999-12-31",
        "remark": "Pastaba",
        "account": 1,
        "expense_type": t.pk,
        "expense_name": n.pk,
    }
    url = reverse("expenses:update", kwargs={"pk": e.pk})

    client_logged.post(url, data, follow=True)

    actual = models.Expense.objects.get(pk=e.pk)
    assert actual.date == date(1999, 12, 31)
    assert actual.price == 15_000
    assert actual.quantity == 33
    assert actual.account.title == "Account1"
    assert actual.expense_type.title == "XXX"
    assert actual.expense_name.title == "YYY"
    assert actual.remark == "Pastaba"


def test_expenses_not_load_other_journal(client_logged, second_user):
    a1 = AccountFactory(title="a1")
    a2 = AccountFactory(journal=second_user.journal, title="a2")
    et1 = ExpenseTypeFactory(title="xxx")
    et2 = ExpenseTypeFactory(title="yyy", journal=second_user.journal)

    ExpenseFactory(expense_type=et1, account=a1)
    e2 = ExpenseFactory(expense_type=et2, account=a2, price=666)

    url = reverse("expenses:update", kwargs={"pk": e2.pk})
    response = client_logged.get(url)

    form = response.content.decode("utf-8")

    assert et2.title not in form
    assert str(e2.price) not in form


@time_machine.travel("2000-03-03")
def test_expenses_update_past_record(main_user, client_logged):
    main_user.year = 2000
    e = ExpenseFactory(date=date(1974, 12, 12))

    data = {
        "price": 0.01,
        "quantity": 33,
        "date": "1998-12-12",
        "remark": "Pastaba",
        "account": 1,
        "expense_type": 1,
        "expense_name": 1,
    }
    url = reverse("expenses:update", kwargs={"pk": e.pk})
    client_logged.post(url, data, follow=True)

    actual = models.Expense.objects.get(pk=e.pk)
    assert actual.date == date(1998, 12, 12)
    assert actual.price == 1
    assert actual.quantity == 33
    assert actual.account.title == "Account1"
    assert actual.expense_type.title == "Expense Type"
    assert actual.expense_name.title == "Expense Name"
    assert actual.remark == "Pastaba"


def test_expenses_index_search_form(client_logged):
    url = reverse("expenses:index")
    response = client_logged.get(url, follow=True).content.decode("utf-8")

    assert '<input type="search" name="search"' in response
    assert reverse("expenses:search") in response


@time_machine.travel("1999-1-1")
def test_expenses_list_month_not_set(client_logged):
    ExpenseFactory(date=date(1998, 1, 1))
    ExpenseFactory(date=date(1999, 1, 1))
    ExpenseFactory(date=date(1999, 2, 1))

    url = reverse("expenses:list")
    actual = client_logged.get(url).context["object_list"]

    assert len(actual) == 1
    assert actual[0]["date"] == date(1999, 1, 1)


@time_machine.travel("1999-1-1")
def test_expenses_list_january(client_logged):
    ExpenseFactory(date=date(1998, 1, 1))
    ExpenseFactory(date=date(1999, 1, 1))
    ExpenseFactory(date=date(1999, 2, 1))

    url = reverse("expenses:list", kwargs={"month": 1})
    actual = client_logged.get(url).context["object_list"]

    assert len(actual) == 1
    assert actual[0]["date"] == date(1999, 1, 1)


@time_machine.travel("1999-1-1")
def test_expenses_list_all(client_logged):
    ExpenseFactory(date=date(1998, 1, 1))
    ExpenseFactory(date=date(1999, 1, 1))
    ExpenseFactory(date=date(1999, 2, 1))

    url = reverse("expenses:list", kwargs={"month": 13})
    actual = client_logged.get(url).context["object_list"]

    assert len(actual) == 2


@time_machine.travel("1999-1-1")
def test_expenses_list_all_any_num(client_logged):
    ExpenseFactory(date=date(1998, 1, 1))
    ExpenseFactory(date=date(1999, 1, 1))
    ExpenseFactory(date=date(1999, 2, 1))

    url = reverse("expenses:list", kwargs={"month": 133})
    actual = client_logged.get(url).context["object_list"]

    assert len(actual) == 2


@time_machine.travel("1999-1-1")
@pytest.mark.usefixtures("mock_mariadb_functions")
def test_expenses_list_price_converted(client_logged):
    ExpenseFactory(price=7777)

    url = reverse("expenses:list", kwargs={"month": 1})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "77,77" in actual


@time_machine.travel("1999-1-1")
@pytest.mark.usefixtures("mock_mariadb_functions")
def test_expenses_list_price_converted_with_thousands(client_logged):
    ExpenseFactory(price=100_000)

    url = reverse("expenses:list", kwargs={"month": 1})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "1.000,00" in actual


# -------------------------------------------------------------------------------------
#                                                                        Expense Delete
# -------------------------------------------------------------------------------------
def test_view_expenses_delete_func():
    view = resolve("/expenses/delete/1/")

    assert expenses.Delete is view.func.view_class


def test_view_expenses_delete_200(client_logged):
    p = ExpenseFactory()

    url = reverse("expenses:delete", kwargs={"pk": p.pk})

    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_expenses_delete_load_form(client_logged):
    p = ExpenseFactory()

    url = reverse("expenses:delete", kwargs={"pk": p.pk})
    response = client_logged.get(url)

    actual = response.content.decode("utf-8")

    assert response.status_code == 200
    assert f'hx-post="{url}"' in actual
    assert '<form method="POST"' in actual
    assert (
        "Ar tikrai norite ištrinti: <strong>1999-01-01/Expense Type/Expense Name</strong>?"  # noqa: E501
        in actual
    )


def test_view_expenses_delete(client_logged):
    p = ExpenseFactory()

    assert models.Expense.objects.all().count() == 1
    url = reverse("expenses:delete", kwargs={"pk": p.pk})

    client_logged.post(url)

    assert models.Expense.objects.all().count() == 0


def test_expenses_delete_other_journal_get_form(client_logged, second_user):
    it2 = ExpenseTypeFactory(title="yyy", journal=second_user.journal)
    i2 = ExpenseFactory(
        expense_type=it2,
        account=AccountFactory(title="A2", journal=second_user.journal),
        price=666,
    )

    url = reverse("expenses:delete", kwargs={"pk": i2.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_expenses_delete_other_journal_post_form(client_logged, second_user):
    it2 = ExpenseTypeFactory(title="yyy", journal=second_user.journal)
    i2 = ExpenseFactory(
        expense_type=it2,
        account=AccountFactory(title="A2", journal=second_user.journal),
        price=666,
    )

    url = reverse("expenses:delete", kwargs={"pk": i2.pk})
    client_logged.post(url)

    assert Expense.objects.all().count() == 1


# -------------------------------------------------------------------------------------
#                                                                           ExpenseType
# -------------------------------------------------------------------------------------
def test_expenses_type_new_func():
    view = resolve("/expenses/type/new/")

    assert expenses_type.New == view.func.view_class


def test_expenses_type_update_func():
    view = resolve("/expenses/type/update/1/")

    assert expenses_type.Update == view.func.view_class


def test_expense_type_not_load_other_journal(client_logged, second_user):
    ExpenseTypeFactory(title="xxx")
    obj = ExpenseTypeFactory(title="yyy", journal=second_user.journal)

    url = reverse("expenses:type_update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    form = response.content.decode("utf-8")

    assert obj.title not in form


def test_expense_type_new_load_form(client_logged):
    url = reverse("expenses:type_new")

    response = client_logged.get(url)

    actual = response.content.decode("utf-8")

    assert f'hx-post="{url}"' in actual


def test_expense_type_updae_load_form(client_logged):
    obj = ExpenseTypeFactory()

    url = reverse("expenses:type_update", kwargs={"pk": obj.pk})

    response = client_logged.get(url)

    actual = response.content.decode("utf-8")

    assert f'hx-post="{url}"' in actual


# -------------------------------------------------------------------------------------
#                                                                           ExpenseName
# -------------------------------------------------------------------------------------
def test_expenses_name_new_func():
    view = resolve("/expenses/name/new/")

    assert expenses_name.New == view.func.view_class


def test_expenses_name_update_func():
    view = resolve("/expenses/name/update/1/")

    assert expenses_name.Update == view.func.view_class


def test_expense_name_new_load_form(client_logged):
    url = reverse("expenses:name_new")
    p = ExpenseTypeFactory()

    response = client_logged.get(url)

    actual = response.content.decode("utf-8")

    assert f'hx-post="{url}"' in actual


def test_expense_name_save_data(client_logged):
    url = reverse("expenses:name_new")
    p = ExpenseTypeFactory()

    data = {"title": "TTT", "parent": p.pk}

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
    e = ExpenseNameFactory(title="XXX")

    url = reverse("expenses:name_update", kwargs={"pk": e.pk})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert f'hx-post="{url}"' in actual
    assert '<input type="text" name="title" value="XXX"' in actual


def test_expense_name_update(client_logged):
    e = ExpenseNameFactory()

    data = {"title": "TTT", "valid_for": 2000, "parent": e.parent.pk}
    url = reverse("expenses:name_update", kwargs={"pk": e.pk})

    response = client_logged.post(url, data, follow=True)

    actual = response.content.decode("utf-8")

    assert "TTT" in actual


def test_expense_name_not_load_other_journal(client_logged, second_user):
    et1 = ExpenseTypeFactory(title="xxx")
    et2 = ExpenseTypeFactory(title="yyy", journal=second_user.journal)

    ExpenseNameFactory(parent=et1)
    obj = ExpenseNameFactory(parent=et2)

    url = reverse("expenses:name_update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    actual = response.content.decode("utf-8")

    assert obj.title not in actual
    assert et2.title not in actual


# -------------------------------------------------------------------------------------
#                                                                       LoadExpenseName
# -------------------------------------------------------------------------------------
def test_load_expenses_name_new_func():
    actual = resolve("/expenses/load_expense_name/")

    assert expenses.LoadExpenseName is actual.func.view_class


def test_load_expense_name_status_code(client_logged):
    url = reverse("expenses:load_expense_name")
    response = client_logged.get(url, {"expense_type": 1})

    assert response.status_code == 200


def test_load_expense_name_isnull_count(client_logged, _db_data):
    change_profile_year(client_logged)

    url = reverse("expenses:load_expense_name")
    response = client_logged.get(url, {"expense_type": 1})

    assert response.context["object_list"].count() == 1


def test_load_expense_name_all(client_logged, _db_data):
    url = reverse("expenses:load_expense_name")
    response = client_logged.get(url, {"expense_type": 1})

    assert response.context["object_list"].count() == 2


def test_load_expense_name_select_empty_parent(client_logged, _db_data):
    url = reverse("expenses:load_expense_name")
    response = client_logged.get(url, {"expense_type": ""})

    assert response.context["object_list"] == []


def test_load_expense_name_must_logged(client):
    url = reverse("expenses:load_expense_name")

    response = client.get(url, follow=True)

    assert response.status_code == 200

    from ...users.views import Login

    assert response.resolver_match.func.view_class is Login


# -------------------------------------------------------------------------------------
#                                                                       Expenses Search
# -------------------------------------------------------------------------------------
def test_search_func():
    view = resolve("/expenses/search/")

    assert expenses.Search == view.func.view_class


def test_search_get_200(client_logged):
    url = reverse("expenses:search")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_search_not_found(client_logged):
    ExpenseFactory()

    url = reverse("expenses:search")
    response = client_logged.get(url, {"search": "xxx"})
    actual = response.content.decode("utf-8")

    assert "Nieko nerasta" in actual


def test_search_found(client_logged):
    ExpenseFactory()

    url = reverse("expenses:search")
    response = client_logged.get(url, {"search": "type"})
    actual = response.content.decode("utf-8")

    assert "1999-01-01" in actual
    assert "Remark" in actual


def test_search_pagination_first_page(client_logged):
    a = AccountFactory()
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory()
    i = ExpenseFactory.build_batch(51, account=a, expense_type=t, expense_name=n)
    Expense.objects.bulk_create(i)

    url = reverse("expenses:search")
    response = client_logged.get(url, {"search": "type"})
    actual = response.context["object_list"]

    assert len(actual) == 50


def test_search_pagination_second_page(client_logged):
    a = AccountFactory()
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory()
    i = ExpenseFactory.build_batch(51, account=a, expense_type=t, expense_name=n)
    Expense.objects.bulk_create(i)

    url = reverse("expenses:search")
    response = client_logged.get(url, {"page": 2, "search": "type"})
    actual = response.context["object_list"]

    assert len(actual) == 1


def test_seach_statistic(client_logged):
    ExpenseFactory(price=100)
    ExpenseFactory(price=200, quantity=2, remark="xxx")
    ExpenseFactory(price=300, quantity=3, remark="xxx")

    url = reverse("expenses:search")
    response = client_logged.get(url, {"page": 2, "search": "xxx"})

    assert response.context["sum_price"] == 500
    assert response.context["sum_quantity"] == 5
    assert response.context["average"] == 100


def test_seach_statistic_not_found(client_logged):
    ExpenseFactory(price=100)
    ExpenseFactory(price=200, quantity=2)
    ExpenseFactory(price=300, quantity=3)

    url = reverse("expenses:search")
    response = client_logged.get(url, {"page": 2, "search": "xxx"})

    assert not response.context["sum_price"]
    assert not response.context["sum_quantity"]
    assert not response.context["average"]
    assert response.context["count"] == 0
