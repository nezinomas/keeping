import re
from datetime import date

import pytest
import time_machine
from django.urls import resolve, reverse

from ...accounts.factories import AccountFactory
from ...savings.factories import SavingTypeFactory
from ...savings.models import SavingType
from .. import models, views
from ..factories import (
    SavingChange,
    SavingChangeFactory,
    SavingClose,
    SavingCloseFactory,
    Transaction,
    TransactionFactory,
)

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                                  Transaction
# ----------------------------------------------------------------------------
def test_view_index_200(client_logged):
    response = client_logged.get("/transactions/")

    assert response.status_code == 200


def test_transactions_index_func():
    view = resolve("/transactions/")

    assert views.Index is view.func.view_class


def test_transactions_lists_func():
    view = resolve("/transactions/lists/")

    assert views.Lists is view.func.view_class


def test_transactions_new_func():
    view = resolve("/transactions/new/")

    assert views.New is view.func.view_class


def test_transactions_update_func():
    view = resolve("/transactions/update/1/")

    assert views.Update is view.func.view_class


def test_transaction_index_context(client_logged):
    url = reverse("transactions:index")
    response = client_logged.get(url)
    context = response.context

    assert "transaction" in context
    assert "saving_close" in context
    assert "saving_change" in context
    assert "account" in context


@time_machine.travel("2000-01-01")
def test_transactions_load_form(client_logged):
    url = reverse("transactions:new")
    response = client_logged.get(url)
    form = response.context["form"]

    assert "1999-01-01" in form.as_p()


def test_transactions_save(client_logged):
    a1 = AccountFactory()
    a2 = AccountFactory(title="Account2")

    data = {
        "date": "1999-01-01",
        "price": "0.01",
        "from_account": a1.pk,
        "to_account": a2.pk,
    }

    url = reverse("transactions:new")
    client_logged.post(url, data)
    actual = Transaction.objects.first()

    assert actual.date == date(1999, 1, 1)
    assert actual.price == 1
    assert actual.from_account.title == "Account1"
    assert actual.to_account.title == "Account2"


def test_transactions_save_invalid_data(client_logged):
    data = {
        "date": "x",
        "price": "x",
        "from_account": 0,
        "to_account": 0,
    }

    url = reverse("transactions:new")
    response = client_logged.post(url, data)
    form = response.context["form"]

    assert not form.is_valid()


def test_transactions_load_update_form_button(client_logged):
    obj = TransactionFactory()

    url = reverse("transactions:update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)
    form = response.content.decode("utf-8")

    assert "Atnaujinti ir uždaryti</button>" in form


def test_transactions_load_update_form_field_values(client_logged):
    obj = TransactionFactory(price=1)

    url = reverse("transactions:update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)
    form = response.context["form"]

    assert form.instance.date == date(1999, 1, 1)
    assert form.instance.price == 0.01

    assert form.instance.from_account.title == "Account1"
    assert form.instance.to_account.title == "Account2"


def test_transactions_update_to_another_year(client_logged):
    tr = TransactionFactory()

    data = {
        "price": "150",
        "date": "2010-12-31",
        "to_account": tr.to_account.pk,
        "from_account": tr.from_account.pk,
    }
    url = reverse("transactions:update", kwargs={"pk": tr.pk})
    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode("utf-8")

    assert "2010-12-31" not in actual


def test_transactions_update(client_logged):
    tr = TransactionFactory()

    data = {
        "price": "150",
        "date": "1999-12-31",
        "from_account": tr.from_account.pk,
        "to_account": tr.to_account.pk,
    }
    url = reverse("transactions:update", kwargs={"pk": tr.pk})
    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode("utf-8")

    assert "1999-12-31" in actual
    assert "Account1" in actual
    assert "Account2" in actual


def test_transactions_not_load_other_journal(client_logged, second_user):
    j2 = second_user.journal
    a_to = AccountFactory(journal=j2, title="a1")
    a_from = AccountFactory(journal=j2, title="a2")

    obj = TransactionFactory(to_account=a_to, from_account=a_from, price=666)
    TransactionFactory()

    url = reverse("transactions:update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_transactions_list_price_converted(client_logged):
    TransactionFactory(price=100_000_000)

    url = reverse("transactions:list")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "1.000.000,00" in actual


# ---------------------------------------------------------------------------------------
#                                                                      Transaction Delete
# ---------------------------------------------------------------------------------------
def test_view_transactions_delete_func():
    view = resolve("/transactions/delete/1/")

    assert views.Delete is view.func.view_class


def test_view_transactions_delete_200(client_logged):
    p = TransactionFactory()

    url = reverse("transactions:delete", kwargs={"pk": p.pk})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_transactions_delete_load_form(client_logged):
    p = TransactionFactory()

    url = reverse("transactions:delete", kwargs={"pk": p.pk})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert '<form method="POST"' in actual
    assert (
        "Ar tikrai norite ištrinti: <strong>1999-01-01 Account1-&gt;Account2: 200</strong>?"
        in actual
    )


def test_view_transactions_delete(client_logged):
    p = TransactionFactory()
    assert models.Transaction.objects.all().count() == 1

    url = reverse("transactions:delete", kwargs={"pk": p.pk})
    client_logged.post(url, follow=True)

    assert models.Transaction.objects.all().count() == 0


def test_transactions_delete_other_journal_get_form(client_logged, second_user):
    j2 = second_user.journal
    a_to = AccountFactory(journal=j2, title="a1")
    a_from = AccountFactory(journal=j2, title="a2")
    obj = TransactionFactory(to_account=a_to, from_account=a_from, price=666)

    url = reverse("transactions:delete", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_transactions_delete_other_journal_post_form(client_logged, second_user):
    j2 = second_user.journal
    a_to = AccountFactory(journal=j2, title="a1")
    a_from = AccountFactory(journal=j2, title="a2")
    obj = TransactionFactory(to_account=a_to, from_account=a_from, price=666)

    url = reverse("transactions:delete", kwargs={"pk": obj.pk})
    client_logged.post(url, follow=True)

    assert Transaction.objects.all().count() == 1


# ----------------------------------------------------------------------------
#                                                                 Saving Close
# ----------------------------------------------------------------------------
def test_saving_close_lists_func():
    view = resolve("/savings_close/lists/")

    assert views.SavingsCloseLists == view.func.view_class


def test_saving_close_new_func():
    view = resolve("/savings_close/new/")

    assert views.SavingsCloseNew == view.func.view_class


def test_saving_close_update_func():
    view = resolve("/savings_close/update/1/")

    assert views.SavingsCloseUpdate == view.func.view_class


@time_machine.travel("2000-01-01")
def test_savings_close_load_form(client_logged):
    url = reverse("transactions:savings_close_new")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "1999-01-01" in actual


def test_savings_close_save(client_logged):
    saving = SavingTypeFactory()
    account = AccountFactory()

    data = {
        "date": "1999-01-01",
        "price": "0.01",
        "fee": "0.01",
        "from_account": saving.pk,
        "to_account": account.pk,
    }
    url = reverse("transactions:savings_close_new")
    client_logged.post(url, data)
    actual = SavingClose.objects.first()

    assert actual.date == date(1999, 1, 1)
    assert actual.price == 1
    assert actual.fee == 1
    assert actual.from_account == saving
    assert actual.to_account == account


def test_savings_close_save_no_fee(client_logged):
    saving = SavingTypeFactory()
    account = AccountFactory()

    data = {
        "date": "1999-01-01",
        "price": "0.01",
        "from_account": saving.pk,
        "to_account": account.pk,
    }
    url = reverse("transactions:savings_close_new")
    client_logged.post(url, data)
    actual = SavingClose.objects.first()

    assert actual.date == date(1999, 1, 1)
    assert actual.price == 1
    assert not actual.fee
    assert actual.from_account == saving
    assert actual.to_account == account


def test_savings_close_save_invalid_data(client_logged):
    data = {
        "date": "x",
        "price": "x",
        "from_account": 0,
        "to_account": 0,
    }
    url = reverse("transactions:savings_close_new")
    response = client_logged.post(url, data)
    form = response.context["form"]

    assert not form.is_valid()


def test_savings_close_load_update_form_field_values(client_logged):
    obj = SavingCloseFactory(price=1, fee=1)

    url = reverse("transactions:savings_close_update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)
    form = response.context["form"]

    assert form.instance.date == date(1999, 1, 1)
    assert form.instance.price == 0.01
    assert form.instance.fee == 0.01

    assert form.instance.from_account.title == "Savings From"
    assert form.instance.to_account.title == "Account To"


def test_savings_close_update_to_another_year(client_logged):
    tr = SavingCloseFactory()

    data = {
        "price": "150",
        "date": "2010-12-31",
        "fee": "99",
        "to_account": tr.to_account.pk,
        "from_account": tr.from_account.pk,
    }
    url = reverse("transactions:savings_close_update", kwargs={"pk": tr.pk})
    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode("utf-8")

    assert "2010-12-31" not in actual


def test_savings_close_update(client_logged):
    obj = SavingCloseFactory()

    data = {
        "price": "0.01",
        "date": "1999-12-31",
        "fee": "0.01",
        "from_account": obj.from_account.pk,
        "to_account": obj.to_account.pk,
    }
    url = reverse("transactions:savings_close_update", kwargs={"pk": obj.pk})
    response = client_logged.post(url, data)
    actual = SavingClose.objects.get(pk=obj.pk)

    assert actual.date == date(1999, 12, 31)
    assert actual.price == 1
    assert actual.fee == 1
    assert actual.to_account.title == "Account To"
    assert actual.from_account.title == "Savings From"


def test_savings_close_update_no_fee(client_logged):
    obj = SavingCloseFactory()

    data = {
        "price": "0.01",
        "date": "1999-12-31",
        "from_account": obj.from_account.pk,
        "to_account": obj.to_account.pk,
    }
    url = reverse("transactions:savings_close_update", kwargs={"pk": obj.pk})
    response = client_logged.post(url, data)
    actual = SavingClose.objects.get(pk=obj.pk)

    assert actual.date == date(1999, 12, 31)
    assert actual.price == 1
    assert not actual.fee
    assert actual.to_account.title == "Account To"
    assert actual.from_account.title == "Savings From"


def test_savings_close_not_load_other_journal(client_logged, second_user):
    j2 = second_user.journal
    a_to = AccountFactory(journal=j2, title="a1")
    a_from = SavingTypeFactory(journal=j2, title="a2")
    obj = SavingCloseFactory(to_account=a_to, from_account=a_from, price=666)
    SavingCloseFactory()

    url = reverse("transactions:savings_close_update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_saving_close_new_checkbox_initial_value(client_logged):
    url = reverse("transactions:savings_close_new")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    reqex = re.compile(r'<input type="checkbox" .*? checked>')
    find = re.findall(reqex, actual)

    assert not find


@time_machine.travel("1999-1-1")
def test_saving_close_load_for_update_checkbox_initial_value(client_logged):
    a = SavingTypeFactory(closed=1999)
    obj = SavingCloseFactory(from_account=a)

    url = reverse("transactions:savings_close_update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    reqex = re.compile(r'<input type="checkbox" .*? checked>')
    find = re.findall(reqex, actual)

    assert len(find) == 1


@time_machine.travel("2000-1-1")
def test_saving_close_update_in_future_checkbox_value(client_logged):
    a = SavingTypeFactory(closed=1999)
    obj = SavingCloseFactory(from_account=a)

    data = {
        "date": obj.date,
        "price": obj.price,
        "fee": obj.fee,
        "from_account": obj.from_account.pk,
        "to_account": obj.to_account.pk,
        "close": True,
    }

    url = reverse("transactions:savings_close_update", kwargs={"pk": obj.pk})
    client_logged.post(url, data)
    actual = SavingType.objects.get(pk=a.pk)

    # closed must not change to 2000
    assert actual.closed == 1999


@time_machine.travel("2000-1-1")
def test_saving_close_update_in_future_checkbox_value_1(client_logged):
    a = SavingTypeFactory()
    obj = SavingCloseFactory(from_account=a)

    data = {
        "date": obj.date,
        "price": obj.price,
        "fee": obj.fee,
        "from_account": obj.from_account.pk,
        "to_account": obj.to_account.pk,
        "close": True,
    }

    url = reverse("transactions:savings_close_update", kwargs={"pk": obj.pk})
    client_logged.post(url, data)
    actual = SavingType.objects.get(pk=a.pk)

    # closed must not change to 2000
    assert actual.closed == 1999


@time_machine.travel("2000-1-1")
def test_saving_close_update_in_future_checkbox_value_uncheck(client_logged):
    a = SavingTypeFactory(closed=1999)
    obj = SavingCloseFactory(from_account=a)

    data = {
        "date": obj.date,
        "price": obj.price,
        "fee": obj.fee,
        "from_account": obj.from_account.pk,
        "to_account": obj.to_account.pk,
        "close": False,
    }

    url = reverse("transactions:savings_close_update", kwargs={"pk": obj.pk})
    client_logged.post(url, data)
    actual = SavingType.objects.get(pk=a.pk)

    assert not actual.closed


def test_saving_close_list_price_converted(client_logged):
    SavingCloseFactory(price=100_000_000, fee=100_000)

    url = reverse("transactions:savings_close_list")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "1.000.000,00" in actual
    assert "1.000,00" in actual


# ---------------------------------------------------------------------------------------
#                                                                      SavingClose Delete
# ---------------------------------------------------------------------------------------
def test_view_savings_close_delete_func():
    view = resolve("/savings_close/delete/1/")

    assert views.SavingsCloseDelete is view.func.view_class


def test_view_savings_close_delete_200(client_logged):
    p = SavingCloseFactory()

    url = reverse("transactions:savings_close_delete", kwargs={"pk": p.pk})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_savings_close_delete_load_form(client_logged):
    p = SavingCloseFactory()

    url = reverse("transactions:savings_close_delete", kwargs={"pk": p.pk})
    response = client_logged.get(url)
    form = response.content.decode("utf-8")

    assert '<form method="POST"' in form
    assert f'hx-post="{url}"' in form
    assert (
        "Ar tikrai norite ištrinti: <strong>1999-01-01 Savings From-&gt;Account To: 10</strong>?"
        in form
    )


def test_view_savings_close_delete(client_logged):
    p = SavingCloseFactory()
    assert models.SavingClose.objects.all().count() == 1

    url = reverse("transactions:savings_close_delete", kwargs={"pk": p.pk})
    client_logged.post(url, follow=True)

    assert models.SavingClose.objects.all().count() == 0


def test_savings_close_delete_other_journal_get_form(client_logged, second_user):
    j2 = second_user.journal
    a_to = AccountFactory(journal=j2, title="a1")
    a_from = SavingTypeFactory(journal=j2, title="a2")
    obj = SavingCloseFactory(to_account=a_to, from_account=a_from, price=666)

    url = reverse("transactions:savings_close_delete", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_savings_close_delete_other_journal_post_form(client_logged, second_user):
    j2 = second_user.journal
    a_to = AccountFactory(journal=j2, title="a1")
    a_from = SavingTypeFactory(journal=j2, title="a2")
    obj = SavingCloseFactory(to_account=a_to, from_account=a_from, price=666)

    url = reverse("transactions:savings_close_delete", kwargs={"pk": obj.pk})
    client_logged.post(url, follow=True)

    assert SavingClose.objects.all().count() == 1


# ----------------------------------------------------------------------------
#                                                                Saving Change
# ----------------------------------------------------------------------------
def test_saving_change_lists_func():
    view = resolve("/savings_change/lists/")

    assert views.SavingsChangeLists == view.func.view_class


def test_saving_change_new_func():
    view = resolve("/savings_change/new/")

    assert views.SavingsChangeNew == view.func.view_class


def test_saving_change_update_func():
    view = resolve("/savings_change/update/1/")

    assert views.SavingsChangeUpdate == view.func.view_class


@time_machine.travel("2000-01-01")
def test_savings_change_load_form(client_logged):
    url = reverse("transactions:savings_change_new")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "1999-01-01" in actual


def test_savings_change_save(client_logged):
    a1 = SavingTypeFactory()
    a2 = SavingTypeFactory(title="Savings2")

    data = {
        "date": "1999-01-01",
        "price": "1",
        "from_account": a1.pk,
        "to_account": a2.pk,
    }
    url = reverse("transactions:savings_change_new")
    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode("utf-8")

    assert "1999-01-01" in actual
    assert "1" in actual
    assert "Savings" in actual
    assert "Savings2" in actual


def test_savings_change_save_invalid_data(client_logged):
    data = {
        "date": "x",
        "price": "x",
        "from_account": 0,
        "to_account": 0,
    }
    url = reverse("transactions:savings_change_new")
    response = client_logged.post(url, data, follow=True)
    form = response.context["form"]

    assert not form.is_valid()


def test_savings_change_not_show_other_journal_types(client_logged, second_user):
    a_from = SavingTypeFactory()
    SavingTypeFactory(title="XXX", journal=second_user.journal)

    data = {
        "date": "1999-01-01",
        "from_account": a_from.pk,
    }
    url = reverse("transactions:savings_change_new")
    response = client_logged.post(url, data, follow=True)
    form = response.context["form"]

    assert not form.is_valid()
    assert "XXX" not in form.as_p()


def test_savings_change_load_update_form_field_values(client_logged):
    obj = SavingChangeFactory(price=1, fee=1)

    url = reverse("transactions:savings_change_update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)
    form = response.context["form"]

    assert form.instance.date == date(1999, 1, 1)
    assert form.instance.price == 0.01
    assert form.instance.fee == 0.01

    assert form.instance.from_account.title == "Savings From"
    assert form.instance.to_account.title == "Savings To"


def test_savings_change_update_to_another_year(client_logged):
    tr = SavingChangeFactory()

    data = {
        "price": "150",
        "date": "2010-12-31",
        "fee": "99",
        "to_account": tr.to_account.pk,
        "from_account": tr.from_account.pk,
    }
    url = reverse("transactions:savings_change_update", kwargs={"pk": tr.pk})
    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode("utf-8")

    assert "2010-12-31" not in actual


def test_savings_change_update(client_logged):
    obj = SavingChangeFactory()

    data = {
        "date": "1999-12-31",
        "price": "0.01",
        "fee": "0.01",
        "from_account": obj.from_account.pk,
        "to_account": obj.to_account.pk,
    }
    url = reverse("transactions:savings_change_update", kwargs={"pk": obj.pk})
    client_logged.post(url, data, follow=True)
    actual = SavingChange.objects.get(pk=obj.pk)

    assert actual.date == date(1999, 12, 31)
    assert actual.price == 1
    assert actual.fee == 1
    assert actual.to_account.title == "Savings To"
    assert actual.from_account.title == "Savings From"


def test_savings_change_update_no_fee(client_logged):
    obj = SavingChangeFactory()

    data = {
        "date": "1999-12-31",
        "price": "0.01",
        "from_account": obj.from_account.pk,
        "to_account": obj.to_account.pk,
    }
    url = reverse("transactions:savings_change_update", kwargs={"pk": obj.pk})
    client_logged.post(url, data, follow=True)
    actual = SavingChange.objects.get(pk=obj.pk)

    assert actual.date == date(1999, 12, 31)
    assert actual.price == 1
    assert not actual.fee
    assert actual.to_account.title == "Savings To"
    assert actual.from_account.title == "Savings From"


def test_savings_change_not_load_other_journal(client_logged, second_user):
    j2 = second_user.journal
    a_to = SavingTypeFactory(journal=j2, title="a1")
    a_from = SavingTypeFactory(journal=j2, title="a2")
    obj = SavingChangeFactory(to_account=a_to, from_account=a_from, price=666)
    SavingChangeFactory()

    url = reverse("transactions:savings_change_update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_saving_change_new_checkbox_initial_value(client_logged):
    url = reverse("transactions:savings_change_new")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    reqex = re.compile(r'<input type="checkbox" .*? checked>')
    find = re.findall(reqex, actual)

    assert not find


@time_machine.travel("1999-1-1")
def test_saving_change_load_for_update_checkbox_initial_value(client_logged):
    a = SavingTypeFactory(closed=1999)
    obj = SavingChangeFactory(from_account=a)

    url = reverse("transactions:savings_change_update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    reqex = re.compile(r'<input type="checkbox" .*? checked>')
    find = re.findall(reqex, actual)

    assert len(find) == 1


@time_machine.travel("2000-1-1")
def test_saving_change_update_in_future_checkbox_value(client_logged):
    a = SavingTypeFactory(closed=1999)
    obj = SavingChangeFactory(from_account=a)

    data = {
        "date": obj.date,
        "price": obj.price,
        "fee": obj.fee,
        "from_account": obj.from_account.pk,
        "to_account": obj.to_account.pk,
        "close": True,
    }

    url = reverse("transactions:savings_change_update", kwargs={"pk": obj.pk})
    client_logged.post(url, data)
    actual = SavingType.objects.get(pk=a.pk)

    # closed must not change to 2000
    assert actual.closed == 1999


@time_machine.travel("2000-1-1")
def test_saving_change_update_in_future_checkbox_value_1(client_logged):
    a = SavingTypeFactory()
    obj = SavingChangeFactory(from_account=a)

    data = {
        "date": obj.date,
        "price": obj.price,
        "fee": obj.fee,
        "from_account": obj.from_account.pk,
        "to_account": obj.to_account.pk,
        "close": True,
    }

    url = reverse("transactions:savings_change_update", kwargs={"pk": obj.pk})
    client_logged.post(url, data)
    actual = SavingType.objects.get(pk=a.pk)

    # closed must not change to 2000
    assert actual.closed == 1999


@time_machine.travel("2000-1-1")
def test_saving_change_update_in_future_checkbox_value_uncheck(client_logged):
    a = SavingTypeFactory(closed=1999)
    obj = SavingChangeFactory(from_account=a)

    data = {
        "date": obj.date,
        "price": obj.price,
        "fee": obj.fee,
        "from_account": obj.from_account.pk,
        "to_account": obj.to_account.pk,
        "close": False,
    }

    url = reverse("transactions:savings_change_update", kwargs={"pk": obj.pk})
    client_logged.post(url, data)
    actual = SavingType.objects.get(pk=a.pk)

    assert not actual.closed


def test_saving_change_list_price_converted(client_logged):
    SavingChangeFactory(price=100_000_000, fee=100_000)

    url = reverse("transactions:savings_change_list")
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "1.000.000,00" in actual
    assert "1.000,00" in actual


# ----------------------------------------------------------------------------
#                                                             load_saving_type
# ----------------------------------------------------------------------------
def test_load_saving_type_func():
    view = resolve("/transactions/load_saving_type/")

    assert views.LoadSavingType is view.func.view_class


def test_load_saving_type_status_code(client_logged):
    url = reverse("transactions:load_saving_type")
    response = client_logged.get(url, {"from_account": 1})

    assert response.status_code == 200


def test_load_saving_type_closed_in_past(client_logged):
    s1 = SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=1000)

    url = reverse("transactions:load_saving_type")
    response = client_logged.get(url, {"from_account": s1.pk})
    actual = response.content.decode("utf-8")

    assert "S1" not in str(actual)
    assert "S2" not in str(actual)


def test_load_saving_type_for_current_user(client_logged, second_user):
    s1 = SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", journal=second_user.journal)

    url = reverse("transactions:load_saving_type")
    response = client_logged.get(url, {"from_account": s1.pk})
    actual = response.content.decode("utf-8")

    assert "S1" not in str(actual)
    assert "S2" not in str(actual)


def test_load_saving_type_empty_parent_pk(client_logged):
    url = reverse("transactions:load_saving_type")
    response = client_logged.get(url, {"from_account": ""})

    assert response.status_code == 200
    assert response.context["object_list"] == []


def test_load_saving_type_must_logged(client):
    url = reverse("transactions:load_saving_type")

    response = client.get(url, follow=True)

    assert response.status_code == 200

    from ...users.views import Login

    assert response.resolver_match.func.view_class is Login


# ---------------------------------------------------------------------------------------
#                                                                      SavingChange Delete
# ---------------------------------------------------------------------------------------
def test_view_savings_change_delete_func():
    view = resolve("/savings_change/delete/1/")

    assert views.SavingsChangeDelete is view.func.view_class


def test_view_savings_change_delete_200(client_logged):
    p = SavingChangeFactory()

    url = reverse("transactions:savings_change_delete", kwargs={"pk": p.pk})
    response = client_logged.get(url)

    assert response.status_code == 200


def test_view_savings_change_delete_load_form(client_logged):
    p = SavingChangeFactory()

    url = reverse("transactions:savings_change_delete", kwargs={"pk": p.pk})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert '<form method="POST"' in actual
    assert f'hx-post="{ url }"' in actual
    assert (
        "Ar tikrai norite ištrinti: <strong>1999-01-01 Savings From-&gt;Savings To: 10</strong>?"
        in actual
    )


def test_view_savings_change_delete(client_logged):
    p = SavingChangeFactory()

    assert models.SavingChange.objects.all().count() == 1

    url = reverse("transactions:savings_change_delete", kwargs={"pk": p.pk})
    client_logged.post(url, follow=True)

    assert models.SavingChange.objects.all().count() == 0


def test_savings_change_delete_other_journal_get_form(client_logged, second_user):
    j2 = second_user.journal
    a_to = SavingTypeFactory(journal=j2, title="a1")
    a_from = SavingTypeFactory(journal=j2, title="a2")

    obj = SavingChangeFactory(to_account=a_to, from_account=a_from, price=666)

    url = reverse("transactions:savings_change_delete", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_savings_change_delete_other_journal_post_form(client_logged, second_user):
    j2 = second_user.journal
    a_to = SavingTypeFactory(journal=j2, title="a1")
    a_from = SavingTypeFactory(journal=j2, title="a2")

    obj = SavingChangeFactory(to_account=a_to, from_account=a_from, price=666)

    url = reverse("transactions:savings_change_delete", kwargs={"pk": obj.pk})
    client_logged.post(url, follow=True)

    assert SavingChange.objects.all().count() == 1
