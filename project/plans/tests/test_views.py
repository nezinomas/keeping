import json

import pytest
import time_machine
from django.urls import resolve, reverse

from ...expenses.tests.factories import ExpenseTypeFactory
from ...incomes.tests.factories import IncomeTypeFactory
from ...savings.tests.factories import SavingTypeFactory
from .. import models, views
from ..services.model_services import (
    IncomePlanModelService,
)
from .factories import (
    DayPlan,
    DayPlanFactory,
    ExpensePlan,
    ExpensePlanFactory,
    IncomePlan,
    IncomePlanFactory,
    NecessaryPlan,
    NecessaryPlanFactory,
    SavingPlan,
    SavingPlanFactory,
)

pytestmark = pytest.mark.django_db


# -------------------------------------------------------------------------------------
#                                                                            Index Plan
# -------------------------------------------------------------------------------------
def test_index_func():
    view = resolve("/plans/")

    assert views.Index == view.func.view_class


def test_index_200(client_logged):
    url = reverse("plans:index")
    response = client_logged.get(url)

    assert response.status_code == 200


def test_index_not_logged(client):
    url = reverse("plans:index")
    response = client.get(url)

    # redirection to login page
    assert response.status_code == 302


# -------------------------------------------------------------------------------------
#                                                                           plans_stats
# -------------------------------------------------------------------------------------
def test_stats_func():
    view = resolve("/plans/stats/")

    assert views.Stats == view.func.view_class


def test_stats_200(client_logged):
    url = reverse("plans:stats")
    response = client_logged.get(url)

    assert response.status_code == 200


# -------------------------------------------------------------------------------------
#                                                              IncomePlan create/update
# -------------------------------------------------------------------------------------
def test_income_new_func():
    view = resolve("/plans/incomes/new/")

    assert views.IncomesNew == view.func.view_class


def test_income_update_func():
    view = resolve("/plans/incomes/update/1999/1/")

    assert views.IncomesUpdate == view.func.view_class


@time_machine.travel("1999-1-1")
def test_income_load_form(client_logged):
    url = reverse("plans:income_new")
    response = client_logged.get(url)
    actual = response.content.decode()

    assert response.status_code == 200
    assert f'hx-post="{url}"' in actual
    assert '<input type="text" name="year" value="1999"' in actual


def test_income_new(client_logged, main_user):
    i = IncomeTypeFactory()
    data = {"year": "1999", "income_type": i.pk, "january": 0.01}

    url = reverse("plans:income_new")
    client_logged.post(url, data, follow=True)
    actual = IncomePlan.objects.first()

    assert actual.journal == main_user.journal
    assert actual.year == 1999
    assert actual.month == 1
    assert actual.price == 1


def test_income_new_invalid_data(client_logged):
    data = {"year": "x", "income_type": 0, "january": 999}

    url = reverse("plans:income_new")
    response = client_logged.post(url, data)
    form = response.context["form"]

    assert not form.is_valid()
    assert "year" in form.errors
    assert "income_type" in form.errors


def test_income_new_prevents_duplicate_category_in_same_year(client_logged, main_user):
    income_type = IncomeTypeFactory(journal=main_user.journal)
    # A plan for this year and type already exists
    IncomePlanFactory(
        year=1999, month=1, income_type=income_type, journal=main_user.journal
    )

    # Try to create ANOTHER plan for the same year and type
    data = {"year": "1999", "income_type": income_type.pk, "january": 9.99}
    url = reverse("plans:income_new")

    response = client_logged.post(url, data)
    form = response.context["form"]

    assert not form.is_valid()
    assert (
        "__all__" in form.errors
    )  # Assuming the error was raised as a non-field error
    assert "1999 metai jau turi Income Type planą." in form.errors["__all__"][0]


def test_income_new_returns_htmx_response(client_logged, main_user):
    income_type = IncomeTypeFactory(journal=main_user.journal)
    data = {"year": "1999", "income_type": income_type.pk, "january": 0.01}

    url = reverse("plans:income_new")

    response = client_logged.post(url, data, HTTP_HX_REQUEST="true")

    assert response.status_code == 204
    assert IncomePlan.objects.filter(year=1999, income_type=income_type).count() == 1

    trigger_header = response.headers.get("HX-Trigger")
    assert trigger_header is not None, "HX-Trigger header is missing!"

    trigger_data = json.loads(trigger_header)
    assert "reloadIncomes" in trigger_data


def test_income_load_update_load_form(client_logged):
    income_type = IncomeTypeFactory()
    IncomePlanFactory(income_type=income_type)

    url = reverse(
        "plans:income_update", kwargs={"year": 1999, "income_type_id": income_type.pk}
    )
    response = client_logged.get(url)
    actual = response.content.decode()

    assert f'hx-post="{url}"' in actual


def test_income_load_update_form_field_values(client_logged):
    income_type = IncomeTypeFactory()
    IncomePlanFactory(income_type=income_type)

    url = reverse(
        "plans:income_update", kwargs={"year": 1999, "income_type_id": income_type.pk}
    )
    response = client_logged.get(url)
    form = response.context["form"]

    assert form.instance.year == 1999
    assert form.instance.income_type.title == "Income Type"

    assert form.initial.get("january") == 0.01
    assert form.initial.get("february") is None
    assert form.initial.get("march") is None
    assert form.initial.get("april") is None
    assert form.initial.get("may") is None
    assert form.initial.get("june") is None
    assert form.initial.get("july") is None
    assert form.initial.get("august") is None
    assert form.initial.get("september") is None
    assert form.initial.get("october") is None
    assert form.initial.get("november") is None
    assert form.initial.get("december") is None


def test_income_update(client_logged):
    obj = IncomePlanFactory(year=1999)

    data = {"year": "1999", "income_type": obj.income_type.pk, "january": 0.05}
    url = reverse(
        "plans:income_update",
        kwargs={"year": 1999, "income_type_id": obj.income_type.pk},
    )
    client_logged.post(url, data)
    actual = IncomePlan.objects.get(pk=obj.pk)

    assert actual.month == 1
    assert actual.price == 5


def test_income_update_returns_htmx_response(client_logged, main_user):
    income_type = IncomeTypeFactory(journal=main_user.journal)

    IncomePlanFactory(
        year=1999,
        income_type=income_type,
        month=1,
        price=1000,
        journal=main_user.journal,
    )

    data = {"year": "1999", "income_type": income_type.pk, "january": 9.99}

    url = reverse(
        "plans:income_update", kwargs={"year": 1999, "income_type_id": income_type.pk}
    )

    response = client_logged.post(url, data, HTTP_HX_REQUEST="true")

    assert response.status_code == 204

    actual = IncomePlan.objects.get(year=1999, income_type=income_type, month=1)
    assert actual.price == 999

    trigger_header = response.headers.get("HX-Trigger")
    assert trigger_header is not None, "HX-Trigger header is missing!"

    trigger_data = json.loads(trigger_header)
    assert "reloadIncomes" in trigger_data


def test_income_update_not_load_other_journal(client_logged, second_user):
    second_user_journal = second_user.journal

    t = IncomeTypeFactory(title="yyy", journal=second_user_journal)
    obj = IncomePlanFactory(
        income_type=t, journal=second_user_journal, month=1, price=666
    )

    url = reverse(
        "plans:income_update", kwargs={"year": 1999, "income_type_id": obj.pk}
    )
    response = client_logged.get(url)

    assert response.status_code == 404


def test_income_list_price_converted_in_template(client_logged):
    income_type = IncomeTypeFactory()
    IncomePlanFactory(income_type=income_type, month=1, price=2)
    IncomePlanFactory(income_type=income_type, month=2, price=2)
    IncomePlanFactory(income_type=income_type, month=3, price=2)
    IncomePlanFactory(income_type=income_type, month=4, price=2)
    IncomePlanFactory(income_type=income_type, month=5, price=2)
    IncomePlanFactory(income_type=income_type, month=6, price=2)
    IncomePlanFactory(income_type=income_type, month=7, price=2)
    IncomePlanFactory(income_type=income_type, month=8, price=2)
    IncomePlanFactory(income_type=income_type, month=9, price=2)
    IncomePlanFactory(income_type=income_type, month=10, price=2)
    IncomePlanFactory(income_type=income_type, month=11, price=2)
    IncomePlanFactory(income_type=income_type, month=12, price=2)

    url = reverse("plans:income_list")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "0,02" in actual
    assert actual.count("0,02") == 12


# -------------------------------------------------------------------------------------
#                                                                     IncomePlan delete
# -------------------------------------------------------------------------------------


def test_incomes_delete_func():
    view = resolve("/plans/incomes/delete/1212/1/")

    assert views.IncomesDelete == view.func.view_class


def test_incomes_delete_200(client_logged):
    obj = IncomePlanFactory()

    url = reverse(
        "plans:income_delete",
        kwargs={"year": 1999, "income_type_id": obj.income_type.pk},
    )
    response = client_logged.get(url)

    assert response.status_code == 200


def test_incomes_delete_load_form(client_logged):
    obj = IncomePlanFactory(year=1999)

    url = reverse(
        "plans:income_delete",
        kwargs={"year": 1999, "income_type_id": obj.income_type.pk},
    )
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert f'hx-post="{url}"' in actual
    assert f"Ar tikrai norite ištrinti: <strong>{obj}</strong>?" in actual


def test_incomes_delete(client_logged):
    income_type = IncomeTypeFactory()
    IncomePlanFactory(year=1999, income_type=income_type, month=1)
    IncomePlanFactory(year=1999, income_type=income_type, month=2)

    assert models.IncomePlan.objects.all().count() == 2

    url = reverse(
        "plans:income_delete", kwargs={"year": 1999, "income_type_id": income_type.pk}
    )

    client_logged.post(url, follow=True)

    assert models.IncomePlan.objects.all().count() == 0


def test_incomes_delete_returns_htmx_response(client_logged):
    income_type = IncomeTypeFactory()
    IncomePlanFactory(year=1999, income_type=income_type, month=1)

    url = reverse(
        "plans:income_delete", kwargs={"year": 1999, "income_type_id": income_type.pk}
    )

    response = client_logged.post(url)

    assert models.IncomePlan.objects.count() == 0
    assert response.status_code in [200, 204]

    trigger_header = response.headers.get("HX-Trigger")
    assert trigger_header is not None, "HX-Trigger header is missing!"

    trigger_data = json.loads(trigger_header)
    assert "reloadIncomes" in trigger_data


def test_incomes_delete_other_journal_get_form(client_logged, second_user):
    second_user_journal = second_user.journal
    income_type = IncomeTypeFactory(title="yyy", journal=second_user_journal)
    obj = IncomePlanFactory(
        income_type=income_type, journal=second_user_journal, month=1, price=666
    )

    url = reverse(
        "plans:income_delete",
        kwargs={"year": 1999, "income_type_id": obj.income_type.pk},
    )
    response = client_logged.get(url)

    assert response.status_code == 404


def test_incomes_delete_other_journal_post_form(client_logged, second_user):
    second_user_journal = second_user.journal
    income_type = IncomeTypeFactory(title="yyy", journal=second_user_journal)
    obj = IncomePlanFactory(
        income_type=income_type, journal=second_user_journal, month=1, price=666
    )

    url = reverse(
        "plans:income_delete",
        kwargs={"year": 1999, "income_type_id": obj.income_type.pk},
    )
    client_logged.post(url)

    assert IncomePlan.objects.all().count() == 1


# -------------------------------------------------------------------------------------
#                                                              ExpensePlan create/update
# -------------------------------------------------------------------------------------
def test_expense_new_func():
    view = resolve("/plans/expenses/new/")

    assert views.ExpensesNew == view.func.view_class


def test_expense_update_func():
    view = resolve("/plans/expenses/update/1999/1/")

    assert views.ExpensesUpdate == view.func.view_class


@time_machine.travel("1999-1-1")
def test_expense_load_form(client_logged):
    url = reverse("plans:expense_new")
    response = client_logged.get(url)
    actual = response.content.decode()

    assert response.status_code == 200
    assert f'hx-post="{url}"' in actual
    assert '<input type="text" name="year" value="1999"' in actual


def test_expense_new(client_logged, main_user):
    i = ExpenseTypeFactory()
    data = {"year": "1999", "expense_type": i.pk, "january": 0.01}

    url = reverse("plans:expense_new")
    client_logged.post(url, data, follow=True)
    actual = ExpensePlan.objects.first()

    assert actual.journal == main_user.journal
    assert actual.year == 1999
    assert actual.month == 1
    assert actual.price == 1


def test_expense_new_invalid_data(client_logged):
    data = {"year": "x", "expense_type": 0, "january": 999}

    url = reverse("plans:expense_new")
    response = client_logged.post(url, data)
    form = response.context["form"]

    assert not form.is_valid()
    assert "year" in form.errors
    assert "expense_type" in form.errors


def test_expense_new_prevents_duplicate_category_in_same_year(client_logged, main_user):
    expense_type = ExpenseTypeFactory(journal=main_user.journal)
    # A plan for this year and type already exists
    ExpensePlanFactory(
        year=1999, month=1, expense_type=expense_type, journal=main_user.journal
    )

    # Try to create ANOTHER plan for the same year and type
    data = {"year": "1999", "expense_type": expense_type.pk, "january": 9.99}
    url = reverse("plans:expense_new")

    response = client_logged.post(url, data)
    form = response.context["form"]

    assert not form.is_valid()
    assert (
        "__all__" in form.errors
    )  # Assuming the error was raised as a non-field error
    assert "1999 metai jau turi Expense Type planą." in form.errors["__all__"][0]


def test_expense_new_returns_htmx_response(client_logged, main_user):
    expense_type = ExpenseTypeFactory(journal=main_user.journal)
    data = {"year": "1999", "expense_type": expense_type.pk, "january": 0.01}

    url = reverse("plans:expense_new")

    response = client_logged.post(url, data, HTTP_HX_REQUEST="true")

    assert response.status_code == 204
    assert ExpensePlan.objects.filter(year=1999, expense_type=expense_type).count() == 1

    trigger_header = response.headers.get("HX-Trigger")
    assert trigger_header is not None, "HX-Trigger header is missing!"

    trigger_data = json.loads(trigger_header)
    assert "reloadExpenses" in trigger_data


def test_expense_load_update_load_form(client_logged):
    expense_type = ExpenseTypeFactory()
    ExpensePlanFactory(expense_type=expense_type)

    url = reverse(
        "plans:expense_update",
        kwargs={"year": 1999, "expense_type_id": expense_type.pk},
    )
    response = client_logged.get(url)
    actual = response.content.decode()

    assert f'hx-post="{url}"' in actual


def test_expense_load_update_form_field_values(client_logged):
    expense_type = ExpenseTypeFactory()
    ExpensePlanFactory(expense_type=expense_type)

    url = reverse(
        "plans:expense_update",
        kwargs={"year": 1999, "expense_type_id": expense_type.pk},
    )
    response = client_logged.get(url)
    form = response.context["form"]

    assert form.instance.year == 1999
    assert form.instance.expense_type.title == "Expense Type"

    assert form.initial.get("january") == 0.01
    assert form.initial.get("february") is None
    assert form.initial.get("march") is None
    assert form.initial.get("april") is None
    assert form.initial.get("may") is None
    assert form.initial.get("june") is None
    assert form.initial.get("july") is None
    assert form.initial.get("august") is None
    assert form.initial.get("september") is None
    assert form.initial.get("october") is None
    assert form.initial.get("november") is None
    assert form.initial.get("december") is None


def test_expense_update(client_logged):
    obj = ExpensePlanFactory(year=1999)

    data = {"year": "1999", "expense_type": obj.expense_type.pk, "january": 0.05}
    url = reverse(
        "plans:expense_update",
        kwargs={"year": 1999, "expense_type_id": obj.expense_type.pk},
    )
    client_logged.post(url, data)
    actual = ExpensePlan.objects.get(pk=obj.pk)

    assert actual.month == 1
    assert actual.price == 5


def test_expense_update_returns_htmx_response(client_logged, main_user):
    expense_type = ExpenseTypeFactory(journal=main_user.journal)

    ExpensePlanFactory(
        year=1999,
        expense_type=expense_type,
        month=1,
        price=1000,
        journal=main_user.journal,
    )

    data = {"year": "1999", "expense_type": expense_type.pk, "january": 9.99}

    url = reverse(
        "plans:expense_update",
        kwargs={"year": 1999, "expense_type_id": expense_type.pk},
    )

    response = client_logged.post(url, data, HTTP_HX_REQUEST="true")

    assert response.status_code == 204

    actual = ExpensePlan.objects.get(year=1999, expense_type=expense_type, month=1)
    assert actual.price == 999

    trigger_header = response.headers.get("HX-Trigger")
    assert trigger_header is not None, "HX-Trigger header is missing!"

    trigger_data = json.loads(trigger_header)
    assert "reloadExpenses" in trigger_data


def test_expense_update_not_load_other_journal(client_logged, second_user):
    second_user_journal = second_user.journal

    t = ExpenseTypeFactory(title="yyy", journal=second_user_journal)
    obj = ExpensePlanFactory(
        expense_type=t, journal=second_user_journal, month=1, price=666
    )

    url = reverse(
        "plans:expense_update", kwargs={"year": 1999, "expense_type_id": obj.pk}
    )
    response = client_logged.get(url)

    assert response.status_code == 404


def test_expense_list_price_converted_in_template(client_logged):
    expense_type = ExpenseTypeFactory()
    ExpensePlanFactory(expense_type=expense_type, month=1, price=2)
    ExpensePlanFactory(expense_type=expense_type, month=2, price=2)
    ExpensePlanFactory(expense_type=expense_type, month=3, price=2)
    ExpensePlanFactory(expense_type=expense_type, month=4, price=2)
    ExpensePlanFactory(expense_type=expense_type, month=5, price=2)
    ExpensePlanFactory(expense_type=expense_type, month=6, price=2)
    ExpensePlanFactory(expense_type=expense_type, month=7, price=2)
    ExpensePlanFactory(expense_type=expense_type, month=8, price=2)
    ExpensePlanFactory(expense_type=expense_type, month=9, price=2)
    ExpensePlanFactory(expense_type=expense_type, month=10, price=2)
    ExpensePlanFactory(expense_type=expense_type, month=11, price=2)
    ExpensePlanFactory(expense_type=expense_type, month=12, price=2)

    url = reverse("plans:expense_list")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "0,02" in actual
    assert actual.count("0,02") == 12


# -------------------------------------------------------------------------------------
#                                                                     ExpensePlan delete
# -------------------------------------------------------------------------------------


def test_expenses_delete_func():
    view = resolve("/plans/expenses/delete/1212/1/")

    assert views.ExpensesDelete == view.func.view_class


def test_expenses_delete_200(client_logged):
    obj = ExpensePlanFactory()

    url = reverse(
        "plans:expense_delete",
        kwargs={"year": 1999, "expense_type_id": obj.expense_type.pk},
    )
    response = client_logged.get(url)

    assert response.status_code == 200


def test_expenses_delete_load_form(client_logged):
    obj = ExpensePlanFactory(year=1999)

    url = reverse(
        "plans:expense_delete",
        kwargs={"year": 1999, "expense_type_id": obj.expense_type.pk},
    )
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert f'hx-post="{url}"' in actual
    assert f"Ar tikrai norite ištrinti: <strong>{obj}</strong>?" in actual


def test_expenses_delete(client_logged):
    expense_type = ExpenseTypeFactory()
    ExpensePlanFactory(year=1999, expense_type=expense_type, month=1)
    ExpensePlanFactory(year=1999, expense_type=expense_type, month=2)

    assert models.ExpensePlan.objects.all().count() == 2

    url = reverse(
        "plans:expense_delete",
        kwargs={"year": 1999, "expense_type_id": expense_type.pk},
    )

    client_logged.post(url, follow=True)

    assert models.ExpensePlan.objects.all().count() == 0


def test_expenses_delete_returns_htmx_response(client_logged):
    expense_type = ExpenseTypeFactory()
    ExpensePlanFactory(year=1999, expense_type=expense_type, month=1)

    url = reverse(
        "plans:expense_delete",
        kwargs={"year": 1999, "expense_type_id": expense_type.pk},
    )

    response = client_logged.post(url)

    assert models.ExpensePlan.objects.count() == 0
    assert response.status_code in [200, 204]

    trigger_header = response.headers.get("HX-Trigger")
    assert trigger_header is not None, "HX-Trigger header is missing!"

    trigger_data = json.loads(trigger_header)
    assert "reloadExpenses" in trigger_data


def test_expenses_delete_other_journal_get_form(client_logged, second_user):
    second_user_journal = second_user.journal
    expense_type = ExpenseTypeFactory(title="yyy", journal=second_user_journal)
    obj = ExpensePlanFactory(
        expense_type=expense_type, journal=second_user_journal, month=1, price=666
    )

    url = reverse(
        "plans:expense_delete",
        kwargs={"year": 1999, "expense_type_id": obj.expense_type.pk},
    )
    response = client_logged.get(url)

    assert response.status_code == 404


def test_expenses_delete_other_journal_post_form(client_logged, second_user):
    second_user_journal = second_user.journal
    expense_type = ExpenseTypeFactory(title="yyy", journal=second_user_journal)
    obj = ExpensePlanFactory(
        expense_type=expense_type, journal=second_user_journal, month=1, price=666
    )

    url = reverse(
        "plans:expense_delete",
        kwargs={"year": 1999, "expense_type_id": obj.expense_type.pk},
    )
    client_logged.post(url)

    assert ExpensePlan.objects.all().count() == 1


# -------------------------------------------------------------------------------------
#                                                              SavingPlan create/update
# -------------------------------------------------------------------------------------
def test_saving_new_func():
    view = resolve("/plans/savings/new/")

    assert views.SavingsNew == view.func.view_class


def test_saving_update_func():
    view = resolve("/plans/savings/update/1999/1/")

    assert views.SavingsUpdate == view.func.view_class


@time_machine.travel("1999-1-1")
def test_saving_load_form(client_logged):
    url = reverse("plans:saving_new")
    response = client_logged.get(url)
    actual = response.content.decode()

    assert response.status_code == 200
    assert f'hx-post="{url}"' in actual
    assert '<input type="text" name="year" value="1999"' in actual


def test_saving_new(client_logged, main_user):
    i = SavingTypeFactory()
    data = {"year": "1999", "saving_type": i.pk, "january": 0.01}

    url = reverse("plans:saving_new")
    client_logged.post(url, data, follow=True)
    actual = SavingPlan.objects.first()

    assert actual.journal == main_user.journal
    assert actual.year == 1999
    assert actual.month == 1
    assert actual.price == 1


def test_saving_new_invalid_data(client_logged):
    data = {"year": "x", "saving_type": 0, "january": 999}

    url = reverse("plans:saving_new")
    response = client_logged.post(url, data)
    form = response.context["form"]

    assert not form.is_valid()
    assert "year" in form.errors
    assert "saving_type" in form.errors


def test_saving_new_prevents_duplicate_category_in_same_year(client_logged, main_user):
    saving_type = SavingTypeFactory(journal=main_user.journal, title="Saving Type")
    # A plan for this year and type already exists
    SavingPlanFactory(
        year=1999, month=1, saving_type=saving_type, journal=main_user.journal
    )

    # Try to create ANOTHER plan for the same year and type
    data = {"year": "1999", "saving_type": saving_type.pk, "january": 9.99}
    url = reverse("plans:saving_new")

    response = client_logged.post(url, data)
    form = response.context["form"]

    assert not form.is_valid()
    assert (
        "__all__" in form.errors
    )  # Assuming the error was raised as a non-field error
    assert "1999 metai jau turi Saving Type planą." in form.errors["__all__"][0]


def test_saving_new_returns_htmx_response(client_logged, main_user):
    saving_type = SavingTypeFactory(journal=main_user.journal)
    data = {"year": "1999", "saving_type": saving_type.pk, "january": 0.01}

    url = reverse("plans:saving_new")

    response = client_logged.post(url, data, HTTP_HX_REQUEST="true")

    assert response.status_code == 204
    assert SavingPlan.objects.filter(year=1999, saving_type=saving_type).count() == 1

    trigger_header = response.headers.get("HX-Trigger")
    assert trigger_header is not None, "HX-Trigger header is missing!"

    trigger_data = json.loads(trigger_header)
    assert "reloadSavings" in trigger_data


def test_saving_load_update_load_form(client_logged):
    saving_type = SavingTypeFactory()
    SavingPlanFactory(saving_type=saving_type)

    url = reverse(
        "plans:saving_update", kwargs={"year": 1999, "saving_type_id": saving_type.pk}
    )
    response = client_logged.get(url)
    actual = response.content.decode()

    assert f'hx-post="{url}"' in actual


def test_saving_load_update_form_field_values(client_logged):
    saving_type = SavingTypeFactory(title="Saving Type")
    SavingPlanFactory(saving_type=saving_type)

    url = reverse(
        "plans:saving_update", kwargs={"year": 1999, "saving_type_id": saving_type.pk}
    )
    response = client_logged.get(url)
    form = response.context["form"]

    assert form.instance.year == 1999
    assert form.instance.saving_type.title == "Saving Type"

    assert form.initial.get("january") == 0.01
    assert form.initial.get("february") is None
    assert form.initial.get("march") is None
    assert form.initial.get("april") is None
    assert form.initial.get("may") is None
    assert form.initial.get("june") is None
    assert form.initial.get("july") is None
    assert form.initial.get("august") is None
    assert form.initial.get("september") is None
    assert form.initial.get("october") is None
    assert form.initial.get("november") is None
    assert form.initial.get("december") is None


def test_saving_update(client_logged):
    obj = SavingPlanFactory(year=1999)

    data = {"year": "1999", "saving_type": obj.saving_type.pk, "january": 0.05}
    url = reverse(
        "plans:saving_update",
        kwargs={"year": 1999, "saving_type_id": obj.saving_type.pk},
    )
    client_logged.post(url, data)
    actual = SavingPlan.objects.get(pk=obj.pk)

    assert actual.month == 1
    assert actual.price == 5


def test_saving_update_returns_htmx_response(client_logged, main_user):
    saving_type = SavingTypeFactory(journal=main_user.journal)

    SavingPlanFactory(
        year=1999,
        saving_type=saving_type,
        month=1,
        price=1000,
        journal=main_user.journal,
    )

    data = {"year": "1999", "saving_type": saving_type.pk, "january": 9.99}

    url = reverse(
        "plans:saving_update", kwargs={"year": 1999, "saving_type_id": saving_type.pk}
    )

    response = client_logged.post(url, data, HTTP_HX_REQUEST="true")

    assert response.status_code == 204

    actual = SavingPlan.objects.get(year=1999, saving_type=saving_type, month=1)
    assert actual.price == 999

    trigger_header = response.headers.get("HX-Trigger")
    assert trigger_header is not None, "HX-Trigger header is missing!"

    trigger_data = json.loads(trigger_header)
    assert "reloadSavings" in trigger_data


def test_saving_update_not_load_other_journal(client_logged, second_user):
    second_user_journal = second_user.journal

    t = SavingTypeFactory(title="yyy", journal=second_user_journal)
    obj = SavingPlanFactory(
        saving_type=t, journal=second_user_journal, month=1, price=666
    )

    url = reverse(
        "plans:saving_update", kwargs={"year": 1999, "saving_type_id": obj.pk}
    )
    response = client_logged.get(url)

    assert response.status_code == 404


def test_saving_list_price_converted_in_template(client_logged):
    saving_type = SavingTypeFactory()
    SavingPlanFactory(saving_type=saving_type, month=1, price=2)
    SavingPlanFactory(saving_type=saving_type, month=2, price=2)
    SavingPlanFactory(saving_type=saving_type, month=3, price=2)
    SavingPlanFactory(saving_type=saving_type, month=4, price=2)
    SavingPlanFactory(saving_type=saving_type, month=5, price=2)
    SavingPlanFactory(saving_type=saving_type, month=6, price=2)
    SavingPlanFactory(saving_type=saving_type, month=7, price=2)
    SavingPlanFactory(saving_type=saving_type, month=8, price=2)
    SavingPlanFactory(saving_type=saving_type, month=9, price=2)
    SavingPlanFactory(saving_type=saving_type, month=10, price=2)
    SavingPlanFactory(saving_type=saving_type, month=11, price=2)
    SavingPlanFactory(saving_type=saving_type, month=12, price=2)

    url = reverse("plans:saving_list")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "0,02" in actual
    assert actual.count("0,02") == 12


# -------------------------------------------------------------------------------------
#                                                                     SavingPlan delete
# -------------------------------------------------------------------------------------


def test_saving_delete_func():
    view = resolve("/plans/savings/delete/1212/1/")

    assert views.SavingsDelete == view.func.view_class


def test_saving_delete_200(client_logged):
    obj = SavingPlanFactory()

    url = reverse(
        "plans:saving_delete",
        kwargs={"year": 1999, "saving_type_id": obj.saving_type.pk},
    )
    response = client_logged.get(url)

    assert response.status_code == 200


def test_saving_delete_load_form(client_logged):
    obj = SavingPlanFactory(year=1999)

    url = reverse(
        "plans:saving_delete",
        kwargs={"year": 1999, "saving_type_id": obj.saving_type.pk},
    )
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert f'hx-post="{url}"' in actual
    assert f"Ar tikrai norite ištrinti: <strong>{obj}</strong>?" in actual


def test_saving_delete(client_logged):
    saving_type = SavingTypeFactory()
    SavingPlanFactory(year=1999, saving_type=saving_type, month=1)
    SavingPlanFactory(year=1999, saving_type=saving_type, month=2)

    assert models.SavingPlan.objects.all().count() == 2

    url = reverse(
        "plans:saving_delete", kwargs={"year": 1999, "saving_type_id": saving_type.pk}
    )

    client_logged.post(url, follow=True)

    assert models.SavingPlan.objects.all().count() == 0


def test_saving_delete_returns_htmx_response(client_logged):
    saving_type = SavingTypeFactory()
    SavingPlanFactory(year=1999, saving_type=saving_type, month=1)

    url = reverse(
        "plans:saving_delete", kwargs={"year": 1999, "saving_type_id": saving_type.pk}
    )

    response = client_logged.post(url)

    assert models.SavingPlan.objects.count() == 0
    assert response.status_code in [200, 204]

    trigger_header = response.headers.get("HX-Trigger")
    assert trigger_header is not None, "HX-Trigger header is missing!"

    trigger_data = json.loads(trigger_header)
    assert "reloadSavings" in trigger_data


def test_saving_delete_other_journal_get_form(client_logged, second_user):
    second_user_journal = second_user.journal
    saving_type = SavingTypeFactory(title="yyy", journal=second_user_journal)
    obj = SavingPlanFactory(
        saving_type=saving_type, journal=second_user_journal, month=1, price=666
    )

    url = reverse(
        "plans:saving_delete",
        kwargs={"year": 1999, "saving_type_id": obj.saving_type.pk},
    )
    response = client_logged.get(url)

    assert response.status_code == 404


def test_saving_delete_other_journal_post_form(client_logged, second_user):
    second_user_journal = second_user.journal
    saving_type = SavingTypeFactory(title="yyy", journal=second_user_journal)
    obj = SavingPlanFactory(
        saving_type=saving_type, journal=second_user_journal, month=1, price=666
    )

    url = reverse(
        "plans:saving_delete",
        kwargs={"year": 1999, "saving_type_id": obj.saving_type.pk},
    )
    client_logged.post(url)

    assert SavingPlan.objects.all().count() == 1


# -------------------------------------------------------------------------------------
#                                                                 DayPlan create/update
# -------------------------------------------------------------------------------------
def test_day_new_func():
    view = resolve("/plans/day/new/")

    assert views.DayNew == view.func.view_class


def test_day_update_func():
    view = resolve("/plans/day/update/1/")

    assert views.DayUpdate == view.func.view_class


@time_machine.travel("1999-1-1")
def test_day(client_logged):
    url = reverse("plans:day_new")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert '<input type="text" name="year" value="1999"' in actual


def test_day_load_form(client_logged):
    url = reverse("plans:day_new")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert f'hx-post="{url}"' in actual


def test_day_new(client_logged, main_user):
    data = {"year": "1999", "january": 0.05}

    url = reverse("plans:day_new")
    client_logged.post(url, data, follow=True)
    actual = DayPlan.objects.first()

    assert actual.journal == main_user.journal
    assert actual.year == 1999
    assert actual.month == 1
    assert actual.price == 5


def test_day_new_dublicates_not_allowed(client_logged, main_user):
    DayPlanFactory(year=1999, month=12, price=100)

    data = {"year": "1999", "january": 0.05}

    url = reverse("plans:day_new")
    response = client_logged.post(url, data)
    form = response.context["form"]

    assert not form.is_valid()


def test_day_invalid_data(client_logged):
    data = {"year": "x", "january": 999}

    url = reverse("plans:day_new")
    response = client_logged.post(url, data)
    form = response.context["form"]

    assert not form.is_valid()


def test_day_load_update_form_field_values(client_logged):
    obj = DayPlanFactory(year=1999, month=1, price=5)

    url = reverse(
        "plans:day_update",
        kwargs={"year": 1999},
    )
    response = client_logged.get(url)
    form = response.context["form"]

    assert form.instance.year == 1999
    assert form.initial.get("january") == 0.05
    assert form.initial.get("february") is None
    assert form.initial.get("march") is None
    assert form.initial.get("april") is None
    assert form.initial.get("may") is None
    assert form.initial.get("june") is None
    assert form.initial.get("july") is None
    assert form.initial.get("august") is None
    assert form.initial.get("september") is None
    assert form.initial.get("october") is None
    assert form.initial.get("november") is None
    assert form.initial.get("december") is None


def test_day_load_update_load_form(client_logged):
    obj = DayPlanFactory()

    url = reverse("plans:day_update", kwargs={"year": 1999})
    response = client_logged.get(url)
    actual = response.content.decode()

    assert f'hx-post="{url}"' in actual


def test_day_update(client_logged):
    obj = DayPlanFactory(year=1999, month=1, price=5)

    data = {"year": "1999", "january": 0.01}
    url = reverse("plans:day_update", kwargs={"year": 1999})

    client_logged.post(url, data, follow=True)
    actual = DayPlan.objects.get(pk=obj.pk)

    assert actual.month == 1


def test_day_update_not_load_other_journal(client_logged, second_user):
    second_user_journal = second_user.journal
    obj = DayPlanFactory(journal=second_user_journal, month=1, price=666)

    url = reverse("plans:day_update", kwargs={"year": 1999})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_day_list_price_converted_in_template(client_logged):
    DayPlanFactory(month=1, price=5)
    DayPlanFactory(month=2, price=5)
    DayPlanFactory(month=3, price=5)
    DayPlanFactory(month=4, price=5)
    DayPlanFactory(month=5, price=5)
    DayPlanFactory(month=6, price=5)
    DayPlanFactory(month=7, price=5)
    DayPlanFactory(month=8, price=5)
    DayPlanFactory(month=9, price=5)
    DayPlanFactory(month=10, price=5)
    DayPlanFactory(month=11, price=5)
    DayPlanFactory(month=12, price=5)

    url = reverse("plans:day_list")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "0,05" in actual
    assert actual.count("0,05") == 12


# -------------------------------------------------------------------------------------
#                                                                        DayPlan delete
# -------------------------------------------------------------------------------------
def test_day_delete_func():
    view = resolve("/plans/day/delete/1/")

    assert views.DayDelete == view.func.view_class


def test_day_delete_200(client_logged):
    p = DayPlanFactory()

    url = reverse("plans:day_delete", kwargs={"year": 1999})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_day_delete_load_form(client_logged):
    p = DayPlanFactory(year=1999)

    url = reverse("plans:day_delete", kwargs={"year": 1999})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert f'hx-post="{url}"' in actual
    assert f"Ar tikrai norite ištrinti: <strong>{p}</strong>?" in actual


def test_day_delete(client_logged):
    DayPlanFactory(year=1999, month=1, price=2)
    DayPlanFactory(year=1999, month=2, price=3)

    assert models.DayPlan.objects.all().count() == 2
    url = reverse("plans:day_delete", kwargs={"year": 1999})

    client_logged.post(url)

    assert models.DayPlan.objects.all().count() == 0


def test_day_delete_other_journal_get_form(client_logged, second_user):
    second_user_journal = second_user.journal
    DayPlanFactory(journal=second_user_journal, month=1, price=666)

    url = reverse("plans:day_delete", kwargs={"year": 1999})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_day_delete_other_journal_post_form(client_logged, second_user):
    second_user_journal = second_user.journal
    DayPlanFactory(journal=second_user_journal, month=1, price=666)

    url = reverse("plans:day_delete", kwargs={"year": 1999})
    client_logged.post(url)

    assert DayPlan.objects.all().count() == 1


# -------------------------------------------------------------------------------------
#                                                           NecessaryPlan create/update
# -------------------------------------------------------------------------------------
def test_necessary_new_func():
    view = resolve("/plans/necessary/new/")

    assert views.NecessaryNew == view.func.view_class


def test_necessary_update_func():
    view = resolve("/plans/necessary/update/1111/66/title/")

    assert views.NecessaryUpdate == view.func.view_class


@time_machine.travel("1999-1-1")
def test_necessary_load_form(client_logged):
    url = reverse("plans:necessary_new")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert f'hx-post="{url}"' in actual
    assert '<input type="text" name="year" value="1999"' in actual


def test_necessary_new(client_logged, main_user):
    e = ExpenseTypeFactory()
    data = {"year": "1999", "title": "X", "january": 0.66, "expense_type": e.pk}

    url = reverse("plans:necessary_new")
    client_logged.post(url, data, follow=True)
    actual = NecessaryPlan.objects.first()

    assert actual.journal == main_user.journal
    assert actual.title == "X"
    assert actual.year == 1999
    assert actual.month == 1
    assert actual.price == 66


def test_necessary_new_dublicates_not_allowed(client_logged, main_user):
    e = ExpenseTypeFactory()
    NecessaryPlanFactory(year=1999, title="XXX", expense_type=e)
    data = {"year": "1999", "title": "XXX", "january": 0.66, "expense_type": e.pk}

    url = reverse("plans:necessary_new")
    response = client_logged.post(url, data)
    form = response.context["form"]

    assert not form.is_valid()


def test_necessary_new_not_load_other_journal(client_logged, second_user):
    this = ExpenseTypeFactory(title="AAA")
    other = ExpenseTypeFactory(journal=second_user.journal, title="XXX")

    url = reverse("plans:necessary_new")
    content = client_logged.get(url).content.decode("utf-8")

    assert this.title in content
    assert other.title not in content


def test_necessary_invalid_data(client_logged):
    data = {"year": "x", "title": "", "january": 999}

    url = reverse("plans:necessary_new")
    response = client_logged.post(url, data)
    form = response.context["form"]

    assert not form.is_valid()


def test_necessary_load_update_load_form(client_logged):
    obj = NecessaryPlanFactory(title="ABCD")

    url = reverse(
        "plans:necessary_update",
        kwargs={"year": 1999, "expense_type_id": obj.expense_type.pk, "title": "ABCD"},
    )
    response = client_logged.get(url)
    actual = response.content.decode()

    assert f'hx-post="{url}"' in actual


def test_necessary_load_update_form_field_values(client_logged):
    obj = NecessaryPlanFactory(title="ABCD", month=11, price=1001)

    url = reverse(
        "plans:necessary_update",
        kwargs={
            "year": 1999,
            "expense_type_id": obj.expense_type.pk,
            "title": obj.title,
        },
    )
    response = client_logged.get(url)
    form = response.context["form"]

    assert form.instance.year == 1999
    assert form.initial.get("january") is None
    assert form.initial.get("february") is None
    assert form.initial.get("march") is None
    assert form.initial.get("april") is None
    assert form.initial.get("may") is None
    assert form.initial.get("june") is None
    assert form.initial.get("july") is None
    assert form.initial.get("august") is None
    assert form.initial.get("september") is None
    assert form.initial.get("october") is None
    assert form.initial.get("november") == 10.01
    assert form.initial.get("december") is None


def test_necessary_update(client_logged):
    obj = NecessaryPlanFactory(year=1999, title="ABCD", month=1, price=666)

    data = {"year": "1999", "title": "X", "january": 0.01}
    url = reverse(
        "plans:necessary_update",
        kwargs={
            "year": 1999,
            "expense_type_id": obj.expense_type.pk,
            "title": obj.title,
        },
    )
    client_logged.post(url, data, follow=True)
    actual = NecessaryPlan.objects.get(pk=obj.pk)

    assert actual.month == 1
    assert actual.price == 1


def test_necessary_update_not_load_other_journal(client_logged, second_user):
    second_journal = second_user.journal
    obj = NecessaryPlanFactory(journal=second_journal, month=1, price=666)

    url = reverse(
        "plans:necessary_update",
        kwargs={
            "year": 1999,
            "expense_type_id": obj.expense_type.pk,
            "title": obj.title,
        },
    )
    response = client_logged.get(url)

    assert response.status_code == 404


def test_necessary_list_price_converted_in_template(client_logged):
    expense_type = ExpenseTypeFactory()
    NecessaryPlanFactory(month=1, price=5)
    NecessaryPlanFactory(month=2, price=5)
    NecessaryPlanFactory(month=3, price=5)
    NecessaryPlanFactory(month=4, price=5)
    NecessaryPlanFactory(month=5, price=5)
    NecessaryPlanFactory(month=6, price=5)
    NecessaryPlanFactory(month=7, price=5)
    NecessaryPlanFactory(month=8, price=5)
    NecessaryPlanFactory(month=9, price=5)
    NecessaryPlanFactory(month=10, price=5)
    NecessaryPlanFactory(month=11, price=5)
    NecessaryPlanFactory(month=12, price=5)

    url = reverse("plans:necessary_list")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "0,05" in actual
    assert actual.count("0,05") == 12


# -------------------------------------------------------------------------------------
#                                                                  NecessaryPlan delete
# -------------------------------------------------------------------------------------
def test_necessary_delete_func():
    view = resolve("/plans/necessary/delete/1234/13/title/")

    assert views.NecessaryDelete == view.func.view_class


def test_necessary_delete_200(client_logged):
    obj = NecessaryPlanFactory()

    url = reverse(
        "plans:necessary_delete",
        kwargs={
            "year": 1999,
            "expense_type_id": obj.expense_type.pk,
            "title": obj.title,
        },
    )
    response = client_logged.get(url)

    assert response.status_code == 200


def test_necessary_delete_load_form(client_logged):
    obj = NecessaryPlanFactory(year=1999)

    url = reverse(
        "plans:necessary_delete",
        kwargs={
            "year": 1999,
            "expense_type_id": obj.expense_type.pk,
            "title": obj.title,
        },
    )
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert f'hx-post="{url}"' in actual
    assert f"Ar tikrai norite ištrinti: <strong>{obj}</strong>?" in actual


def test_necessary_delete(client_logged):
    obj = NecessaryPlanFactory(year=1999, month=1, price=1)
    NecessaryPlanFactory(year=1999, month=2, price=1)
    NecessaryPlanFactory(year=2026, month=2, price=1)

    assert models.NecessaryPlan.objects.all().count() == 3

    url = reverse(
        "plans:necessary_delete",
        kwargs={
            "year": 1999,
            "expense_type_id": obj.expense_type.pk,
            "title": obj.title,
        },
    )
    client_logged.post(url)

    assert models.NecessaryPlan.objects.all().count() == 1

    actual = models.NecessaryPlan.objects.first()
    assert actual.year == 2026


def test_necessary_delete_other_journal_get_form(client_logged, second_user):
    second_user_journal = second_user.journal
    obj = NecessaryPlanFactory(journal=second_user_journal, month=1, price=666)

    url = reverse(
        "plans:necessary_delete",
        kwargs={
            "year": 1999,
            "expense_type_id": obj.expense_type.pk,
            "title": obj.title,
        },
    )
    response = client_logged.get(url)

    assert response.status_code == 404


def test_necessary_delete_other_journal_post_form(client_logged, second_user):
    second_user_journal = second_user.journal
    obj = NecessaryPlanFactory(journal=second_user_journal, month=1, price=666)

    url = reverse(
        "plans:necessary_delete",
        kwargs={
            "year": 1999,
            "expense_type_id": obj.expense_type.pk,
            "title": obj.title,
        },
    )
    client_logged.post(url)

    assert NecessaryPlan.objects.all().count() == 1


# # -------------------------------------------------------------------------------------
# #                                                                            Copy Plans
# # -------------------------------------------------------------------------------------
# def test_copy_func():
#     view = resolve("/plans/copy/")

#     assert views.CopyPlans is view.func.view_class


# def test_copy_200(client_logged):
#     response = client_logged.get("/plans/copy/")

#     assert response.status_code == 200


# def test_copy_success(main_user, client_logged):
#     IncomePlanFactory(year=1999)
#     data = {"year_from": "1999", "year_to": "2000", "income": True}

#     url = reverse("plans:copy")
#     client_logged.post(url, data, follow=True)

#     actual = IncomePlanModelService(main_user).year(2000)

#     assert actual[0].year == 2000


# def test_copy_fails(client_logged):
#     data = {"year_from": "1999", "year_to": "2000", "income": True}

#     url = reverse("plans:copy")
#     response = client_logged.post(url, data)
#     form = response.context["form"]

#     assert not form.is_valid()


# def test_copy_year_to_same_as_user_year(main_user, client_logged):
#     IncomePlanFactory(year=1999)

#     main_user.year = 2000
#     main_user.save()

#     data = {"year_from": "1999", "year_to": "2000", "income": True}

#     url = reverse("plans:copy")
#     response = client_logged.post(url, data)

#     assert response.headers["HX-Trigger"]
#     assert "afterCopy" in response.headers["HX-Trigger"]
