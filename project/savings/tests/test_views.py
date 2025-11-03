from datetime import date

import pytest
import time_machine
from django.urls import resolve, reverse

from ...accounts.factories import AccountFactory
from ...core.tests.utils import clean_content
from .. import models, views
from ..factories import Saving, SavingFactory, SavingTypeFactory

pytestmark = pytest.mark.django_db


def test_index_func():
    view = resolve("/savings/")

    assert views.Index == view.func.view_class


def test_savings_lists_func():
    view = resolve("/savings/lists/")

    assert views.Lists == view.func.view_class


def test_savings_new_func():
    view = resolve("/savings/new/")

    assert views.New == view.func.view_class


def test_savings_update_func():
    view = resolve("/savings/update/1/")

    assert views.Update == view.func.view_class


def test_types_lists_func():
    view = resolve("/savings/type/")

    assert views.TypeLists == view.func.view_class


def test_types_new_func():
    view = resolve("/savings/type/new/")

    assert views.TypeNew == view.func.view_class


def test_types_update_func():
    view = resolve("/savings/type/update/1/")

    assert views.TypeUpdate == view.func.view_class


def test_index_view_context(client_logged):
    url = reverse("savings:index")
    response = client_logged.get(url)
    context = response.context

    assert "saving" in context
    assert "saving_type" in context
    assert "pension" in context
    assert "pension_type" in context


@time_machine.travel("2000-01-01")
def test_saving_load_new_form(client_logged):
    url = reverse("savings:new")

    response = client_logged.get(url)

    actual = response.content.decode("utf-8")

    assert "1999-01-01" in actual


@time_machine.travel("1999-1-1")
def test_saving_save(client_logged):
    a = AccountFactory()
    i = SavingTypeFactory()

    data = {
        "date": "1999-01-01",
        "price": "0.01",
        "fee": "2",
        "account": a.pk,
        "saving_type": i.pk,
    }

    url = reverse("savings:new")

    response = client_logged.post(url, data, follow=True)

    actual = response.content.decode("utf-8")

    assert "1999-01-01" in actual
    assert "1" in actual
    assert "2" in actual
    assert "Account1" in actual
    assert "Savings" in actual


def test_saving_save_invalid_data(client_logged):
    data = {"date": "x", "price": "x", "fee": "x", "account": "x", "saving_type": "x"}

    url = reverse("savings:new")

    response = client_logged.post(url, data)

    actual = response.context["form"]

    assert not actual.is_valid()
    assert "date" in actual.errors
    assert "price" in actual.errors
    assert "fee" in actual.errors
    assert "account" in actual.errors
    assert "saving_type" in actual.errors


def test_savings_load_update_form_button(client_logged):
    obj = SavingFactory()

    url = reverse("savings:update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)
    form = response.content.decode("utf-8")

    assert "Atnaujinti ir uždaryti</button>" in clean_content(form)


def test_savings_load_update_form_field_values(client_logged):
    obj = SavingFactory(price=1, fee=1)

    url = reverse("savings:update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)
    form = response.context["form"]

    assert form.instance.date == date(1999, 1, 1)
    assert form.instance.price == 0.01
    assert form.instance.fee == 0.01
    assert form.instance.account.title == "Account1"
    assert form.instance.saving_type.title == "Savings"
    assert form.instance.remark == "remark"


def test_savings_load_update_form_field_values_fee_none(client_logged):
    obj = SavingFactory(price=1, fee=None)

    url = reverse("savings:update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)
    form = response.context["form"]

    assert form.instance.date == date(1999, 1, 1)
    assert form.instance.price == 0.01
    assert not form.instance.fee
    assert form.instance.account.title == "Account1"
    assert form.instance.saving_type.title == "Savings"
    assert form.instance.remark == "remark"


@time_machine.travel("2011-1-1")
def test_saving_update_to_another_year(client_logged):
    saving = SavingFactory()

    data = {
        "price": "150",
        "date": "2010-12-31",
        "remark": "Pastaba",
        "fee": "25",
        "account": 1,
        "saving_type": 1,
    }
    url = reverse("savings:update", kwargs={"pk": saving.pk})

    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode("utf-8")

    assert "2010-12-31" not in actual


@time_machine.travel("1999-12-31")
def test_saving_update(client_logged):
    saving = SavingFactory()

    data = {
        "price": "0.01",
        "fee": "0.01",
        "date": "1999-12-31",
        "remark": "Pastaba",
        "account": 1,
        "saving_type": 1,
    }
    url = reverse("savings:update", kwargs={"pk": saving.pk})

    client_logged.post(url, data, follow=True)
    actual = Saving.objects.get(pk=saving.pk)

    assert actual.date == date(1999, 12, 31)
    assert actual.price == 1
    assert actual.fee == 1
    assert actual.remark == "Pastaba"


@time_machine.travel("1999-12-31")
def test_saving_update_fee_with_489(client_logged):
    saving = SavingFactory()

    data = {
        "price": "0.01",
        "fee": "4.89",
        "date": "1999-12-31",
        "remark": "Pastaba",
        "account": 1,
        "saving_type": 1,
    }
    url = reverse("savings:update", kwargs={"pk": saving.pk})

    client_logged.post(url, data, follow=True)
    actual = Saving.objects.get(pk=saving.pk)

    assert actual.date == date(1999, 12, 31)
    assert actual.price == 1
    assert actual.fee == 489
    assert actual.remark == "Pastaba"


def test_savings_not_load_other_journal(client_logged, second_user):
    a1 = AccountFactory(title="a1")
    a2 = AccountFactory(journal=second_user.journal, title="a2")

    it1 = SavingTypeFactory(title="xxx")
    it2 = SavingTypeFactory(title="yyy", journal=second_user.journal)

    SavingFactory(saving_type=it1, account=a1)
    i2 = SavingFactory(saving_type=it2, account=a2, price=666)

    url = reverse("savings:update", kwargs={"pk": i2.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_savings_list_price_converted(client_logged):
    SavingFactory(price=7777, fee=8888)

    url = reverse("savings:list")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "77,77" in actual
    assert "88,88" in actual


@time_machine.travel("1999-1-1")
def test_savings_list_price_converted_with_thousands(client_logged):
    SavingFactory(price=100_000_000, fee=100_000)

    url = reverse("savings:list")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "1.000.000,00" in actual
    assert "1.000,00" in actual


# -------------------------------------------------------------------------------------
#                                                                         Saving Delete
# -------------------------------------------------------------------------------------
def test_view_saving_delete_func():
    view = resolve("/savings/delete/1/")

    assert views.Delete is view.func.view_class


def test_view_saving_delete_200(client_logged):
    p = SavingFactory()

    url = reverse("savings:delete", kwargs={"pk": p.pk})

    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_saving_delete_load_form(client_logged):
    p = SavingFactory()

    url = reverse("savings:delete", kwargs={"pk": p.pk})
    response = client_logged.get(url)

    form = response.content.decode("utf-8")

    assert '<form method="POST"' in form
    assert f'hx-post="{url}"' in form
    assert "Ar tikrai norite ištrinti: <strong>1999-01-01: Savings</strong>?" in form


def test_view_saving_delete(client_logged):
    p = SavingFactory()

    assert models.Saving.objects.all().count() == 1
    url = reverse("savings:delete", kwargs={"pk": p.pk})

    client_logged.post(url, follow=True)

    assert models.Saving.objects.all().count() == 0


def test_savings_delete_other_journal_get_form(client_logged, second_user):
    it2 = SavingTypeFactory(title="yyy", journal=second_user.journal)
    i2 = SavingFactory(
        saving_type=it2,
        account=AccountFactory(title="A2", journal=second_user.journal),
        price=666,
    )

    url = reverse("savings:delete", kwargs={"pk": i2.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_savings_delete_other_journal_post_form(client_logged, second_user):
    it2 = SavingTypeFactory(title="yyy", journal=second_user.journal)
    i2 = SavingFactory(
        saving_type=it2,
        account=AccountFactory(title="A2", journal=second_user.journal),
        price=666,
    )

    url = reverse("savings:delete", kwargs={"pk": i2.pk})
    client_logged.post(url, follow=True)

    assert Saving.objects.all().count() == 1


# ----------------------------------------------------------------------------
#                                                                  Saving Type
# ----------------------------------------------------------------------------
@time_machine.travel("2000-01-01")
def test_type_load_form(client_logged):
    url = reverse("savings:type_new")

    response = client_logged.get(url)

    assert response.status_code == 200


def test_type_save(client_logged):
    data = {
        "title": "TTT",
        "type": "funds",
    }

    url = reverse("savings:type_new")

    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode("utf-8")

    assert "TTT" in actual


def test_type_save_with_closed(client_logged):
    data = {
        "title": "TTT",
        "closed": "2000",
        "type": "shares",
    }

    url = reverse("savings:type_new")

    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode("utf-8")

    assert "TTT" in actual


def test_type_save_invalid_data(client_logged):
    data = {"title": ""}

    url = reverse("savings:type_new")

    response = client_logged.post(url, data, follow=True)

    actual = response.context["form"]

    assert not actual.is_valid()


def test_type_update(client_logged):
    saving = SavingTypeFactory()

    data = {
        "title": "TTT",
        "type": "funds",
    }
    url = reverse("savings:type_update", kwargs={"pk": saving.pk})

    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode("utf-8")

    assert "TTT" in actual


def test_type_update_return_list_with_closed(client_logged):
    SavingTypeFactory(title="YYY", closed="1111")
    saving = SavingTypeFactory(title="XXX")

    data = {
        "title": "TTT",
        "type": "funds",
    }
    url = reverse("savings:type_update", kwargs={"pk": saving.pk})

    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode("utf-8")

    assert "TTT" in actual
    assert "YYY" not in actual
    assert "XXX" not in actual


def test_saving_type_not_load_other_journal(client_logged, second_user):
    SavingTypeFactory(title="xxx")
    obj = SavingTypeFactory(title="yyy", journal=second_user.journal)

    url = reverse("savings:type_update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    actual = response.content.decode("utf-8")

    assert obj.title not in actual


def test_type_update_with_closed(client_logged):
    saving = SavingTypeFactory()

    data = {
        "title": "TTT",
        "closed": "2000",
        "type": "pensions",
    }
    url = reverse("savings:type_update", kwargs={"pk": saving.pk})

    response = client_logged.post(url, data, follow=True)

    actual = response.content.decode("utf-8")

    assert "TTT" in actual


@pytest.mark.django_db
def test_view_index_200(client_logged):
    response = client_logged.get("/savings/")

    assert response.status_code == 200


@pytest.mark.django_db
def test_type_list_view_has_all(client_logged):
    SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=1974)

    url = reverse("savings:type_list")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "S1" in actual
    assert "S2" in actual
