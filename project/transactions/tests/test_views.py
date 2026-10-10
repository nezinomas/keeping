import re
from datetime import date
from typing import NamedTuple

import pytest
import time_machine
from django.urls import reverse

from ...accounts.tests.factories import AccountFactory
from ...core.tests.utils import clean_content
from ...savings.models import SavingType
from ...savings.tests.factories import SavingTypeFactory
from ...users.views import Login
from .. import models
from .factories import (
    SavingChangeFactory,
    SavingClose,
    SavingCloseFactory,
    Transaction,
    TransactionFactory,
)

pytestmark = pytest.mark.django_db


class Kind(NamedTuple):
    factory: type
    model: type
    to_factory: type
    from_factory: type
    new_url: str
    update_url: str
    delete_url: str
    to_title: str
    delete_text: str


KINDS = {
    "transactions": Kind(
        TransactionFactory,
        models.Transaction,
        AccountFactory,
        AccountFactory,
        "transactions:new",
        "transactions:update",
        "transactions:delete",
        "Account2",
        "1999-01-01 Account1 -&gt; Account2: 2,00",
    ),
    "savings_close": Kind(
        SavingCloseFactory,
        models.SavingClose,
        AccountFactory,
        SavingTypeFactory,
        "transactions:savings_close_new",
        "transactions:savings_close_update",
        "transactions:savings_close_delete",
        "Account To",
        "1999-01-01 Savings From -&gt; Account To: 0,10",
    ),
    "savings_change": Kind(
        SavingChangeFactory,
        models.SavingChange,
        SavingTypeFactory,
        SavingTypeFactory,
        "transactions:savings_change_new",
        "transactions:savings_change_update",
        "transactions:savings_change_delete",
        "Savings To",
        "1999-01-01 Savings From -&gt; Savings To: 0,10",
    ),
}
by_kind = pytest.mark.parametrize("kind", KINDS.values(), ids=KINDS.keys())
by_fund_move = pytest.mark.parametrize(
    "kind",
    [KINDS["savings_close"], KINDS["savings_change"]],
    ids=["savings_close", "savings_change"],
)


@pytest.mark.parametrize(
    "rendered",
    [
        pytest.param("1.111,00", id="transaction"),
        pytest.param("2.222,00", id="saving_close"),
        pytest.param("3.333,00", id="saving_change"),
        pytest.param("Lonely", id="account"),
    ],
)
def test_index_renders_its_four_lists(client_logged, rendered):
    TransactionFactory(price=111_100)
    SavingCloseFactory(price=222_200)
    SavingChangeFactory(price=333_300)
    AccountFactory(title="Lonely")

    response = client_logged.get(reverse("transactions:index"))

    assert rendered in response.content.decode("utf-8")


@by_kind
@time_machine.travel("2000-01-01")
def test_load_form(client_logged, kind):
    url = reverse(kind.new_url)
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "1999-01-01" in actual
    assert url in actual


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


@pytest.mark.parametrize(
    "kind, follow",
    [
        pytest.param(KINDS["transactions"], False, id="transactions"),
        pytest.param(KINDS["savings_close"], False, id="savings_close"),
        pytest.param(KINDS["savings_change"], True, id="savings_change"),
    ],
)
def test_save_invalid_data(client_logged, kind, follow):
    data = {
        "date": "x",
        "price": "x",
        "from_account": 0,
        "to_account": 0,
    }

    response = client_logged.post(reverse(kind.new_url), data, follow=follow)
    form = response.context["form"]

    assert not form.is_valid()


@pytest.mark.parametrize(
    "kind, kwargs",
    [
        pytest.param(KINDS["transactions"], {}, id="transactions"),
        pytest.param(
            KINDS["savings_close"], {"price": 1, "fee": 1}, id="savings_close"
        ),
        pytest.param(
            KINDS["savings_change"], {"price": 1, "fee": 1}, id="savings_change"
        ),
    ],
)
def test_load_update_form(client_logged, kind, kwargs):
    obj = kind.factory(**kwargs)

    url = reverse(kind.update_url, kwargs={"pk": obj.pk})
    response = client_logged.get(url)
    actual = clean_content(response.content.decode("utf-8"))

    assert "Atnaujinti ir uždaryti</button>" in actual
    assert url in actual


def test_transactions_load_update_form_field_values(client_logged):
    obj = TransactionFactory(price=1)

    url = reverse("transactions:update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)
    form = response.context["form"].as_p()

    assert 'name="date" value="1999-01-01"' in form
    assert 'name="price" value="0.01"' in form
    assert f'<option value="{obj.from_account.pk}" selected>Account1</option>' in form
    assert f'<option value="{obj.to_account.pk}">Account2</option>' in form
    assert f'<option value="{obj.to_account.pk}" selected>Account2</option>' in form


@pytest.mark.parametrize(
    "kind, extra",
    [
        pytest.param(KINDS["transactions"], {}, id="transactions"),
        pytest.param(KINDS["savings_close"], {"fee": "99"}, id="savings_close"),
        pytest.param(KINDS["savings_change"], {"fee": "99"}, id="savings_change"),
    ],
)
def test_update_to_another_year(client_logged, kind, extra):
    tr = kind.factory()

    data = {
        "price": "150",
        "date": "2010-12-31",
        "to_account": tr.to_account.pk,
        "from_account": tr.from_account.pk,
    } | extra
    url = reverse(kind.update_url, kwargs={"pk": tr.pk})
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


@pytest.mark.parametrize(
    "kind, extra",
    [
        pytest.param(KINDS["transactions"], {"price": "150"}, id="transactions"),
        pytest.param(
            KINDS["savings_change"],
            {"price": "0.01", "fee": "0.01"},
            id="savings_change",
        ),
    ],
)
def test_update_switch_accounts(client_logged, kind, extra):
    obj = kind.factory()
    old_from, old_to = obj.from_account_id, obj.to_account_id

    data = {
        "date": "1999-12-31",
        "from_account": old_to,
        "to_account": old_from,
    } | extra
    url = reverse(kind.update_url, kwargs={"pk": obj.pk})
    client_logged.post(url, data)
    actual = kind.model.objects.get(pk=obj.pk)

    assert actual.from_account_id == old_to
    assert actual.to_account_id == old_from


def _foreign_move(kind, journal):
    return kind.factory(
        to_account=kind.to_factory(journal=journal, title="a1"),
        from_account=kind.from_factory(journal=journal, title="a2"),
        price=666,
    )


@by_kind
def test_not_load_other_journal(client_logged, second_user, kind):
    obj = _foreign_move(kind, second_user.journal)
    kind.factory()

    url = reverse(kind.update_url, kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


@pytest.mark.parametrize(
    "url_name, factory, kwargs, expected",
    [
        pytest.param(
            "transactions:list",
            TransactionFactory,
            {"price": 100_000_000},
            ("1.000.000,00",),
            id="transactions",
        ),
        pytest.param(
            "transactions:savings_close_list",
            SavingCloseFactory,
            {"price": 100_000_000, "fee": 100_000},
            ("1.000.000,00", "1.000,00"),
            id="savings_close",
        ),
        pytest.param(
            "transactions:savings_change_list",
            SavingChangeFactory,
            {"price": 100_000_000, "fee": 100_000},
            ("1.000.000,00", "1.000,00"),
            id="savings_change",
        ),
    ],
)
def test_list_price_converted(client_logged, url_name, factory, kwargs, expected):
    factory(**kwargs)

    response = client_logged.get(reverse(url_name))
    actual = response.content.decode("utf-8")

    for text in expected:
        assert text in actual


@by_kind
def test_delete_load_form(client_logged, kind):
    p = kind.factory()

    url = reverse(kind.delete_url, kwargs={"pk": p.pk})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert url in actual
    assert '<form method="POST"' in actual
    assert f'hx-post="{url}"' in actual
    assert f"Ar tikrai norite ištrinti: <strong>{kind.delete_text}</strong>?" in actual


@by_kind
def test_delete(client_logged, kind):
    p = kind.factory()
    assert kind.model.objects.count() == 1

    url = reverse(kind.delete_url, kwargs={"pk": p.pk})
    client_logged.post(url, follow=True)

    assert kind.model.objects.count() == 0


@by_kind
def test_delete_other_journal_get_form(client_logged, second_user, kind):
    obj = _foreign_move(kind, second_user.journal)

    url = reverse(kind.delete_url, kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


@by_kind
def test_delete_other_journal_post_form(client_logged, second_user, kind):
    obj = _foreign_move(kind, second_user.journal)

    url = reverse(kind.delete_url, kwargs={"pk": obj.pk})
    client_logged.post(url, follow=True)

    assert kind.model.objects.count() == 1


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


by_fund_move_follow = pytest.mark.parametrize(
    "kind, follow",
    [
        pytest.param(KINDS["savings_close"], False, id="savings_close"),
        pytest.param(KINDS["savings_change"], True, id="savings_change"),
    ],
)


@by_fund_move_follow
def test_update(client_logged, kind, follow):
    obj = kind.factory()

    data = {
        "price": "0.01",
        "date": "1999-12-31",
        "fee": "0.01",
        "from_account": obj.from_account.pk,
        "to_account": obj.to_account.pk,
    }
    url = reverse(kind.update_url, kwargs={"pk": obj.pk})
    client_logged.post(url, data, follow=follow)
    actual = kind.model.objects.get(pk=obj.pk)

    assert actual.date == date(1999, 12, 31)
    assert actual.price == 1
    assert actual.fee == 1
    assert actual.to_account.title == kind.to_title
    assert actual.from_account.title == "Savings From"


@by_fund_move_follow
def test_update_no_fee(client_logged, kind, follow):
    obj = kind.factory()

    data = {
        "price": "0.01",
        "date": "1999-12-31",
        "from_account": obj.from_account.pk,
        "to_account": obj.to_account.pk,
    }
    url = reverse(kind.update_url, kwargs={"pk": obj.pk})
    client_logged.post(url, data, follow=follow)
    actual = kind.model.objects.get(pk=obj.pk)

    assert actual.date == date(1999, 12, 31)
    assert actual.price == 1
    assert not actual.fee
    assert actual.to_account.title == kind.to_title
    assert actual.from_account.title == "Savings From"


@by_fund_move
def test_new_form_close_checkbox_is_unchecked(client_logged, kind):
    response = client_logged.get(reverse(kind.new_url))
    actual = response.content.decode("utf-8")

    reqex = re.compile(r'<input type="checkbox" .*? checked>')
    find = re.findall(reqex, actual)

    assert not find


@by_fund_move
@time_machine.travel("1999-1-1")
def test_load_for_update_checkbox_initial_value(client_logged, kind):
    a = SavingTypeFactory(closed=1999)
    obj = kind.factory(from_account=a)

    url = reverse(kind.update_url, kwargs={"pk": obj.pk})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    reqex = re.compile(r'<input type="checkbox" .*? checked>')
    find = re.findall(reqex, actual)

    assert len(find) == 1


@by_fund_move
@pytest.mark.parametrize("closed", [1999, None], ids=["closed", "open"])
@time_machine.travel("2000-1-1")
def test_update_in_future_checkbox_value(client_logged, kind, closed):
    a = SavingTypeFactory(closed=closed)
    obj = kind.factory(from_account=a)

    data = {
        "date": obj.date,
        "price": obj.price,
        "fee": obj.fee,
        "from_account": obj.from_account.pk,
        "to_account": obj.to_account.pk,
        "close": True,
    }

    url = reverse(kind.update_url, kwargs={"pk": obj.pk})
    client_logged.post(url, data)
    actual = SavingType.objects.get(pk=a.pk)

    # closed must not change to 2000
    assert actual.closed == 1999


@by_fund_move
@time_machine.travel("2000-1-1")
def test_update_in_future_checkbox_value_uncheck(client_logged, kind):
    a = SavingTypeFactory(closed=1999)
    obj = kind.factory(from_account=a)

    data = {
        "date": obj.date,
        "price": obj.price,
        "fee": obj.fee,
        "from_account": obj.from_account.pk,
        "to_account": obj.to_account.pk,
        "close": False,
    }

    url = reverse(kind.update_url, kwargs={"pk": obj.pk})
    client_logged.post(url, data)
    actual = SavingType.objects.get(pk=a.pk)

    assert not actual.closed


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
    form = response.context["form"].as_p()

    assert 'name="date" value="1999-01-01"' in form
    assert 'name="price" value="0.01"' in form
    assert 'name="fee" value="0.01"' in form

    assert (
        f'<option value="{obj.from_account.pk}" selected>Savings From</option>' in form
    )
    assert f'<option value="{obj.to_account.pk}">Savings To</option>' in form
    assert f'<option value="{obj.to_account.pk}" selected>Savings To</option>' in form


def test_load_saving_type_lists_the_open_funds_except_the_source(client_logged):
    s1 = SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=1000)
    s3 = SavingTypeFactory(title="S3")

    url = reverse("transactions:load_saving_type")
    response = client_logged.get(url, {"from_account": s1.pk})
    actual = response.content.decode("utf-8")

    assert "S1" not in actual
    assert "S2" not in actual
    assert f'<option value="{s3.pk}">S3</option>' in actual


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
    assert response.resolver_match.func.view_class is Login
