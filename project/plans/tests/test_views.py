import pytest
import time_machine
from django.urls import resolve, reverse

from ...expenses.factories import ExpenseTypeFactory
from ...incomes.factories import IncomeTypeFactory
from ...savings.factories import SavingTypeFactory
from .. import models, views
from ..factories import (
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
from ..services.model_services import ModelService


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
    view = resolve("/plans/incomes/update/1/")

    assert views.IncomesUpdate == view.func.view_class


@time_machine.travel("1999-1-1")
def test_income_load_form(client_logged):
    url = reverse("plans:income_new")
    response = client_logged.get(url)
    actual = response.context["form"].as_p()

    assert response.status_code == 200
    assert '<input type="text" name="year" value="1999"' in actual


def test_income_new(client_logged):
    i = IncomeTypeFactory()
    data = {"year": "1999", "income_type": i.pk, "january": 0.01}

    url = reverse("plans:income_new")
    client_logged.post(url, data, follow=True)
    actual = IncomePlan.objects.first()

    assert actual.january == 1


def test_income_invalid_data(client_logged):
    data = {"year": "x", "income_type": 0, "january": 999}

    url = reverse("plans:income_new")
    response = client_logged.post(url, data)
    form = response.context["form"]

    assert not form.is_valid()


def test_income_load_update_form_field_values(client_logged):
    obj = IncomePlanFactory()

    url = reverse("plans:income_update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)
    form = response.context["form"]

    assert form.instance.year == 1999
    assert form.instance.january == 0.01
    assert form.instance.february == 0.01
    assert form.instance.march == 0.01
    assert form.instance.april == 0.01
    assert form.instance.may == 0.01
    assert form.instance.june == 0.01
    assert form.instance.july == 0.01
    assert form.instance.august == 0.01
    assert form.instance.september == 0.01
    assert form.instance.october == 0.01
    assert form.instance.november == 0.01
    assert form.instance.december == 0.01
    assert form.instance.income_type.title == "Income Type"


def test_income_update(client_logged):
    obj = IncomePlanFactory(year=1999)

    data = {"year": "1999", "income_type": obj.income_type.pk, "january": 0.01}
    url = reverse("plans:income_update", kwargs={"pk": obj.pk})
    client_logged.post(url, data)
    actual = IncomePlan.objects.get(pk=obj.pk)

    assert actual.january == 1


def test_income_update_unique_together_user_change_year(client_logged):
    IncomePlanFactory(year=2000)
    p = IncomePlanFactory(year=1999)

    data = {"year": "2000", "income_type": p.income_type.pk, "january": 999}
    url = reverse("plans:income_update", kwargs={"pk": p.pk})
    response = client_logged.post(url, data)
    form = response.context["form"]

    assert not form.is_valid()


def test_income_update_not_load_other_journal(client_logged, second_user):
    j = second_user.journal
    t = IncomeTypeFactory(title="yyy", journal=j)
    obj = IncomePlanFactory(income_type=t, journal=j, january=666)

    url = reverse("plans:income_update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_income_list_price_converted_in_template(client_logged):
    IncomePlanFactory()

    url = reverse("plans:income_list")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "0,01" in actual
    assert actual.count("0,01") == 12


# -------------------------------------------------------------------------------------
#                                                                     IncomePlan delete
# -------------------------------------------------------------------------------------
def test_incomes_delete_func():
    view = resolve("/plans/incomes/delete/1/")

    assert views.IncomesDelete == view.func.view_class


def test_incomes_delete_200(client_logged):
    p = IncomePlanFactory()

    url = reverse("plans:income_delete", kwargs={"pk": p.pk})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_incomes_delete_load_form(client_logged):
    p = IncomePlanFactory(year=1999)

    url = reverse("plans:income_delete", kwargs={"pk": p.pk})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert f"Ar tikrai norite ištrinti: <strong>{p}</strong>?" in actual


def test_incomes_delete(client_logged):
    p = IncomePlanFactory(year=1999)

    assert models.IncomePlan.objects.all().count() == 1
    url = reverse("plans:income_delete", kwargs={"pk": p.pk})

    client_logged.post(url, follow=True)

    assert models.IncomePlan.objects.all().count() == 0


def test_incomes_delete_other_journal_get_form(client_logged, second_user):
    j = second_user.journal
    t = IncomeTypeFactory(title="yyy", journal=j)
    obj = IncomePlanFactory(income_type=t, journal=j, january=666)

    url = reverse("plans:income_delete", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_incomes_delete_other_journal_post_form(client_logged, second_user):
    j = second_user.journal
    t = IncomeTypeFactory(title="yyy", journal=j)
    obj = IncomePlanFactory(income_type=t, journal=j, january=666)

    url = reverse("plans:income_delete", kwargs={"pk": obj.pk})
    client_logged.post(url)

    assert IncomePlan.objects.all().count() == 1


# -------------------------------------------------------------------------------------
#                                                            ExpensesPlan create/update
# -------------------------------------------------------------------------------------
def test_expense_new_func():
    view = resolve("/plans/expenses/new/")

    assert views.ExpensesNew == view.func.view_class


def test_expense_update_func():
    view = resolve("/plans/expenses/update/1/")

    assert views.ExpensesUpdate == view.func.view_class


@time_machine.travel("1999-1-1")
def test_expense_load_form(client_logged):
    url = reverse("plans:expense_new")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert '<input type="text" name="year" value="1999"' in actual


def test_expense_new(client_logged):
    i = ExpenseTypeFactory()
    data = {"year": "1999", "expense_type": i.pk, "january": 0.01}

    url = reverse("plans:expense_new")
    client_logged.post(url, data, follow=True)
    client_logged.post(url, data, follow=True)
    actual = ExpensePlan.objects.first()

    assert actual.january == 1


def test_expense_invalid_data(client_logged):
    data = {"year": "x", "expense_type": 0, "january": 999}

    url = reverse("plans:expense_new")
    response = client_logged.post(url, data)
    form = response.context["form"]

    assert not form.is_valid()


def test_expense_load_update_form_field_values(client_logged):
    obj = ExpensePlanFactory()

    url = reverse("plans:expense_update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)
    form = response.context["form"]

    assert form.instance.year == 1999
    assert form.instance.january == 0.01
    assert form.instance.february == 0.01
    assert form.instance.march == 0.01
    assert form.instance.april == 0.01
    assert form.instance.may == 0.01
    assert form.instance.june == 0.01
    assert form.instance.july == 0.01
    assert form.instance.august == 0.01
    assert form.instance.september == 0.01
    assert form.instance.october == 0.01
    assert form.instance.november == 0.01
    assert form.instance.december == 0.01
    assert form.instance.expense_type.title == "Expense Type"


def test_expense_update(client_logged):
    obj = ExpensePlanFactory(year=1999)

    data = {"year": "1999", "expense_type": obj.expense_type.pk, "january": 0.01}
    url = reverse("plans:expense_update", kwargs={"pk": obj.pk})

    client_logged.post(url, data, follow=True)
    actual = ExpensePlan.objects.get(pk=obj.pk)

    assert actual.january == 1


def test_expense_update_unique_together_user_change_year(client_logged):
    ExpensePlanFactory(year=2000)
    p = ExpensePlanFactory(year=1999)

    data = {"year": "2000", "expense_type": p.expense_type.pk, "january": 999}

    url = reverse("plans:expense_update", kwargs={"pk": p.pk})
    response = client_logged.post(url, data)
    form = response.context["form"]

    assert not form.is_valid()


def test_expense_update_not_load_other_journal(client_logged, second_user):
    j = second_user.journal
    t = ExpenseTypeFactory(title="yyy", journal=j)
    obj = ExpensePlanFactory(expense_type=t, journal=j, january=666)

    url = reverse("plans:expense_update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_expense_list_price_converted_in_template(client_logged):
    ExpensePlanFactory()

    url = reverse("plans:expense_list")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "0,01" in actual
    assert actual.count("0,01") == 12


# -------------------------------------------------------------------------------------
#                                                                   ExpensesPlan delete
# -------------------------------------------------------------------------------------
def test_expense_delete_func():
    view = resolve("/plans/expenses/delete/1/")

    assert views.ExpensesDelete == view.func.view_class


def test_expense_delete_200(client_logged):
    p = ExpensePlanFactory()

    url = reverse("plans:expense_delete", kwargs={"pk": p.pk})

    response = client_logged.get(url)

    assert response.status_code == 200


def test_expense_delete_load_form(client_logged):
    p = ExpensePlanFactory(year=1999)

    url = reverse("plans:expense_delete", kwargs={"pk": p.pk})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert f"Ar tikrai norite ištrinti: <strong>{p}</strong>?" in actual


def test_expense_delete(client_logged):
    p = ExpensePlanFactory(year=1999)

    assert models.ExpensePlan.objects.all().count() == 1
    url = reverse("plans:expense_delete", kwargs={"pk": p.pk})
    client_logged.post(url)

    assert models.ExpensePlan.objects.all().count() == 0


def test_expense_delete_other_journal_get_form(client_logged, second_user):
    j = second_user.journal
    t = ExpenseTypeFactory(title="yyy", journal=j)
    obj = ExpensePlanFactory(expense_type=t, journal=j, january=666)

    url = reverse("plans:expense_delete", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_expense_delete_other_journal_post_form(client_logged, second_user):
    j = second_user.journal
    t = ExpenseTypeFactory(title="yyy", journal=j)
    obj = ExpensePlanFactory(expense_type=t, journal=j, january=666)

    url = reverse("plans:expense_delete", kwargs={"pk": obj.pk})
    client_logged.post(url)

    assert ExpensePlan.objects.all().count() == 1


# -------------------------------------------------------------------------------------
#                                                              SavingPlan create/update
# -------------------------------------------------------------------------------------
def test_saving_new_func():
    view = resolve("/plans/savings/new/")

    assert views.SavingsNew == view.func.view_class


def test_saving_update_func():
    view = resolve("/plans/savings/update/1/")

    assert views.SavingsUpdate == view.func.view_class


@time_machine.travel("1999-1-1")
def test_saving_year_input(client_logged):
    url = reverse("plans:saving_new")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert '<input type="text" name="year" value="1999"' in actual


def test_saving_new(client_logged):
    i = SavingTypeFactory()
    data = {"year": "1999", "saving_type": i.pk, "january": 0.01}

    url = reverse("plans:saving_new")
    response = client_logged.post(url, data, follow=True)
    actual = SavingPlan.objects.first()

    assert actual.january == 1


def test_saving_invalid_data(client_logged):
    data = {"year": "x", "saving_type": 0, "january": 999}

    url = reverse("plans:saving_new")
    response = client_logged.post(url, data)
    form = response.context["form"]

    assert not form.is_valid()


def test_saving_load_update_form_field_values(client_logged):
    obj = SavingPlanFactory()

    url = reverse("plans:saving_update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)
    form = response.context["form"]

    assert form.instance.year == 1999
    assert form.instance.january == 0.01
    assert form.instance.february == 0.01
    assert form.instance.march == 0.01
    assert form.instance.april == 0.01
    assert form.instance.may == 0.01
    assert form.instance.june == 0.01
    assert form.instance.july == 0.01
    assert form.instance.august == 0.01
    assert form.instance.september == 0.01
    assert form.instance.october == 0.01
    assert form.instance.november == 0.01
    assert form.instance.december == 0.01
    assert form.instance.saving_type.title == "Savings"


def test_saving_update(client_logged):
    obj = SavingPlanFactory(year=1999)

    data = {"year": "1999", "saving_type": obj.saving_type.pk, "january": 0.01}
    url = reverse("plans:saving_update", kwargs={"pk": obj.pk})
    client_logged.post(url, data, follow=True)
    actual = SavingPlan.objects.get(pk=obj.pk)

    assert actual.january == 1


def test_saving_update_unique_together_user_change_year(client_logged):
    SavingPlanFactory(year=2000)
    p = SavingPlanFactory(year=1999)

    data = {"year": "2000", "saving_type": p.saving_type.pk, "january": 999}
    url = reverse("plans:saving_update", kwargs={"pk": p.pk})

    response = client_logged.post(url, data)
    form = response.context["form"]

    assert not form.is_valid()


def test_saving_update_not_load_other_journal(client_logged, second_user):
    j = second_user.journal
    t = SavingTypeFactory(title="yyy", journal=j)
    obj = SavingPlanFactory(saving_type=t, journal=j, january=666)

    url = reverse("plans:saving_update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_saving_list_price_converted_in_template(client_logged):
    SavingPlanFactory()

    url = reverse("plans:saving_list")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "0,01" in actual
    assert actual.count("0,01") == 12


# -------------------------------------------------------------------------------------
#                                                                     SavingPlan delete
# -------------------------------------------------------------------------------------
def test_saving_delete_func():
    view = resolve("/plans/savings/delete/1/")

    assert views.SavingsDelete == view.func.view_class


def test_saving_delete_200(client_logged):
    p = SavingPlanFactory()

    url = reverse("plans:saving_delete", kwargs={"pk": p.pk})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_saving_delete_load_form(client_logged):
    p = SavingPlanFactory(year=1999)

    url = reverse("plans:saving_delete", kwargs={"pk": p.pk})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert f"Ar tikrai norite ištrinti: <strong>{p}</strong>?" in actual


def test_saving_delete(client_logged):
    p = SavingPlanFactory(year=1999)

    assert models.SavingPlan.objects.all().count() == 1
    url = reverse("plans:saving_delete", kwargs={"pk": p.pk})

    client_logged.post(url)

    assert models.SavingPlan.objects.all().count() == 0


def test_saving_delete_other_journal_get_form(client_logged, second_user):
    j = second_user.journal
    t = SavingTypeFactory(title="yyy", journal=j)
    obj = SavingPlanFactory(saving_type=t, journal=j, january=666)

    url = reverse("plans:saving_delete", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_saving_delete_other_journal_post_form(client_logged, second_user):
    j = second_user.journal
    t = SavingTypeFactory(title="yyy", journal=j)
    obj = SavingPlanFactory(saving_type=t, journal=j, january=666)

    url = reverse("plans:saving_delete", kwargs={"pk": obj.pk})
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


def test_day_new(client_logged):
    data = {"year": "1999", "january": 0.01}

    url = reverse("plans:day_new")
    client_logged.post(url, data, follow=True)
    actual = DayPlan.objects.first()

    assert actual.january == 1


def test_day_invalid_data(client_logged):
    data = {"year": "x", "january": 999}

    url = reverse("plans:day_new")
    response = client_logged.post(url, data)
    form = response.context["form"]

    assert not form.is_valid()


def test_day_load_update_form_field_values(client_logged):
    obj = DayPlanFactory()

    url = reverse("plans:day_update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)
    form = response.context["form"]

    assert form.instance.year == 1999
    assert form.instance.january == 0.01
    assert form.instance.february == 0.01
    assert form.instance.march == 0.01
    assert form.instance.april == 0.01
    assert form.instance.may == 0.01
    assert form.instance.june == 0.01
    assert form.instance.july == 0.01
    assert form.instance.august == 0.01
    assert form.instance.september == 0.01
    assert form.instance.october == 0.01
    assert form.instance.november == 0.01
    assert form.instance.december == 0.01


def test_day_update(client_logged):
    obj = DayPlanFactory(year=1999)

    data = {"year": "1999", "january": 0.01}
    url = reverse("plans:day_update", kwargs={"pk": obj.pk})

    client_logged.post(url, data, follow=True)
    actual = DayPlan.objects.get(pk=obj.pk)

    assert actual.january == 1


def test_day_update_unique_together_user_change_year(client_logged):
    DayPlanFactory(year=2000)
    p = DayPlanFactory(year=1999)

    data = {"year": "2000", "january": 999}
    url = reverse("plans:day_update", kwargs={"pk": p.pk})
    response = client_logged.post(url, data)
    form = response.context["form"]

    assert not form.is_valid()


def test_day_update_not_load_other_journal(client_logged, second_user):
    j = second_user.journal
    obj = DayPlanFactory(journal=j, january=666)

    url = reverse("plans:day_update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_day_list_price_converted_in_template(client_logged):
    DayPlanFactory()

    url = reverse("plans:day_list")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "0,01" in actual
    assert actual.count("0,01") == 12


# -------------------------------------------------------------------------------------
#                                                                        DayPlan delete
# -------------------------------------------------------------------------------------
def test_day_delete_func():
    view = resolve("/plans/day/delete/1/")

    assert views.DayDelete == view.func.view_class


def test_day_delete_200(client_logged):
    p = DayPlanFactory()

    url = reverse("plans:day_delete", kwargs={"pk": p.pk})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_day_delete_load_form(client_logged):
    p = DayPlanFactory(year=1999)

    url = reverse("plans:day_delete", kwargs={"pk": p.pk})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert f"Ar tikrai norite ištrinti: <strong>{p}</strong>?" in actual


def test_day_delete(client_logged):
    p = DayPlanFactory(year=1999)

    assert models.DayPlan.objects.all().count() == 1
    url = reverse("plans:day_delete", kwargs={"pk": p.pk})

    client_logged.post(url)

    assert models.DayPlan.objects.all().count() == 0


def test_day_delete_other_journal_get_form(client_logged, second_user):
    j = second_user.journal
    obj = DayPlanFactory(journal=j, january=666)

    url = reverse("plans:day_delete", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_day_delete_other_journal_post_form(client_logged, second_user):
    j = second_user.journal
    obj = DayPlanFactory(journal=j, january=666)

    url = reverse("plans:day_delete", kwargs={"pk": obj.pk})
    client_logged.post(url)

    assert DayPlan.objects.all().count() == 1


# -------------------------------------------------------------------------------------
#                                                           NecessaryPlan create/update
# -------------------------------------------------------------------------------------
def test_necessary_new_func():
    view = resolve("/plans/necessary/new/")

    assert views.NecessaryNew == view.func.view_class


def test_necessary_update_func():
    view = resolve("/plans/necessary/update/1/")

    assert views.NecessaryUpdate == view.func.view_class


@time_machine.travel("1999-1-1")
def test_necessary(client_logged):
    url = reverse("plans:necessary_new")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert '<input type="text" name="year" value="1999"' in actual


def test_necessary_new(client_logged):
    e = ExpenseTypeFactory()
    data = {"year": "1999", "title": "X", "january": 0.01, "expense_type": e.pk}

    url = reverse("plans:necessary_new")
    client_logged.post(url, data, follow=True)
    actual = NecessaryPlan.objects.first()

    assert actual.january == 1


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


def test_necessary_load_update_form_field_values(client_logged):
    obj = NecessaryPlanFactory()

    url = reverse("plans:necessary_update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)
    form = response.context["form"]

    assert form.instance.year == 1999
    assert form.instance.january == 0.01
    assert form.instance.february == 0.01
    assert form.instance.march == 0.01
    assert form.instance.april == 0.01
    assert form.instance.may == 0.01
    assert form.instance.june == 0.01
    assert form.instance.july == 0.01
    assert form.instance.august == 0.01
    assert form.instance.september == 0.01
    assert form.instance.october == 0.01
    assert form.instance.november == 0.01
    assert form.instance.december == 0.01


def test_necessary_update(client_logged):
    obj = NecessaryPlanFactory(year=1999)

    data = {"year": "1999", "title": "X", "january": 0.01}
    url = reverse("plans:necessary_update", kwargs={"pk": obj.pk})
    client_logged.post(url, data, follow=True)
    actual = NecessaryPlan.objects.get(pk=obj.pk)

    assert actual.january == 1


def test_necessary_update_unique_together_user_change_year(client_logged):
    NecessaryPlanFactory(year=2000, title="XXX")
    p = NecessaryPlanFactory(year=1999, title="XXX")

    data = {"year": "2000", "title": "XXX", "january": 999}
    url = reverse("plans:necessary_update", kwargs={"pk": p.pk})
    response = client_logged.post(url, data)
    form = response.context["form"]

    assert not form.is_valid()


def test_necessary_update_not_load_other_journal(client_logged, second_user):
    j = second_user.journal
    obj = NecessaryPlanFactory(journal=j, january=666)

    url = reverse("plans:necessary_update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_necessary_list_price_converted_in_template(client_logged):
    NecessaryPlanFactory()

    url = reverse("plans:necessary_list")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "0,01" in actual
    assert actual.count("0,01") == 12


# -------------------------------------------------------------------------------------
#                                                                  NecessaryPlan delete
# -------------------------------------------------------------------------------------
def test_necessary_delete_func():
    view = resolve("/plans/necessary/delete/1/")

    assert views.NecessaryDelete == view.func.view_class


def test_necessary_delete_200(client_logged):
    p = NecessaryPlanFactory()

    url = reverse("plans:necessary_delete", kwargs={"pk": p.pk})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_necessary_delete_load_form(client_logged):
    p = NecessaryPlanFactory(year=1999)

    url = reverse("plans:necessary_delete", kwargs={"pk": p.pk})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert f"Ar tikrai norite ištrinti: <strong>{p}</strong>?" in actual


def test_necessary_delete(client_logged):
    p = NecessaryPlanFactory(year=1999)
    assert models.NecessaryPlan.objects.all().count() == 1

    url = reverse("plans:necessary_delete", kwargs={"pk": p.pk})
    client_logged.post(url)

    assert models.NecessaryPlan.objects.all().count() == 0


def test_necessary_delete_other_journal_get_form(client_logged, second_user):
    j = second_user.journal
    obj = ExpensePlanFactory(journal=j, january=666)

    url = reverse("plans:necessary_delete", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_necessary_delete_other_journal_post_form(client_logged, second_user):
    j = second_user.journal
    obj = NecessaryPlanFactory(journal=j, january=666)

    url = reverse("plans:necessary_delete", kwargs={"pk": obj.pk})
    client_logged.post(url)

    assert NecessaryPlan.objects.all().count() == 1


# -------------------------------------------------------------------------------------
#                                                                            Copy Plans
# -------------------------------------------------------------------------------------
def test_copy_func():
    view = resolve("/plans/copy/")

    assert views.CopyPlans is view.func.view_class


def test_copy_200(client_logged):
    response = client_logged.get("/plans/copy/")

    assert response.status_code == 200


def test_copy_success(main_user, client_logged):
    IncomePlanFactory(year=1999)
    data = {"year_from": "1999", "year_to": "2000", "income": True}

    url = reverse("plans:copy")
    client_logged.post(url, data, follow=True)

    actual = ModelService(models.IncomePlan, main_user).year(2000)

    assert actual[0].year == 2000


def test_copy_fails(client_logged):
    data = {"year_from": "1999", "year_to": "2000", "income": True}

    url = reverse("plans:copy")
    response = client_logged.post(url, data)
    form = response.context["form"]

    assert not form.is_valid()


def test_copy_year_to_same_as_user_year(main_user, client_logged):
    IncomePlanFactory(year=1999)

    main_user.year = 2000
    main_user.save()

    data = {"year_from": "1999", "year_to": "2000", "income": True}

    url = reverse("plans:copy")
    response = client_logged.post(url, data)

    assert response.headers["HX-Trigger"]
    assert "afterCopy" in response.headers["HX-Trigger"]
