import re
from datetime import date
from functools import partial
from typing import NamedTuple

import pytest
import time_machine
from django.urls import reverse

from ...accounts.tests.factories import AccountFactory
from ...core.tests.utils import clean_content, view_for
from ...savings.models import SavingBalance, SavingType
from ...savings.tests.factories import SavingFactory, SavingTypeFactory
from ...users.views import Login
from .. import models, views
from .factories import SavingChangeFactory, SavingCloseFactory, TransactionFactory

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
    from_title: str
    modal_title: str


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
        "Account1",
        "Pinigų pervedimas",
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
        "Savings From",
        "Fondas ⇒ Sąskaita",
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
        "Savings From",
        "Fondas ⇔ Fondas",
    ),
}
by_kind = pytest.mark.parametrize("kind", KINDS.values(), ids=KINDS.keys())
by_fund_move = pytest.mark.parametrize(
    "kind",
    [KINDS["savings_close"], KINDS["savings_change"]],
    ids=["savings_close", "savings_change"],
)
CHECKED_BOX = re.compile(r'<input type="checkbox" .*? checked>')


@pytest.mark.parametrize(
    "rendered",
    [
        pytest.param("1.111,00", id="transaction"),
        pytest.param("2.222,00", id="saving_close"),
        pytest.param("3.333,00", id="saving_change"),
        pytest.param("Lonely", id="account"),
        pytest.param("<h6>Sąskaita ⇔ Sąskaita</h6>", id="account_heading"),
        pytest.param("<h6>Fondas ⇒ Sąskaita</h6>", id="saving_close_heading"),
        pytest.param("<h6>Fondas ⇔ Fondas</h6>", id="saving_change_heading"),
    ],
)
def test_index_renders_its_lists_and_headings(client_logged, rendered):
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
    assert f'<h5 class="modal-title">{kind.modal_title}</h5>' in actual


def _post_new(client_logged, kind, **extra):
    a_from = kind.from_factory(title="From")
    a_to = kind.to_factory(title="To")
    data = {
        "date": "1999-01-01",
        "price": "0.01",
        "from_account": a_from.pk,
        "to_account": a_to.pk,
    } | extra

    client_logged.post(reverse(kind.new_url), data)

    return kind.model.objects.get(), a_from, a_to


def _assert_saved(actual, a_from, a_to):
    assert actual.date == date(1999, 1, 1)
    assert actual.price == 1
    assert actual.from_account == a_from
    assert actual.to_account == a_to


@by_kind
def test_save(client_logged, kind):
    _assert_saved(*_post_new(client_logged, kind))


@by_fund_move
@pytest.mark.parametrize(
    "posted, cents",
    [pytest.param({"fee": "0.01"}, 1, id="fee"), pytest.param({}, 0, id="no_fee")],
)
def test_save_fee(client_logged, kind, posted, cents):
    actual, a_from, a_to = _post_new(client_logged, kind, **posted)

    _assert_saved(actual, a_from, a_to)
    assert actual.fee == cents


@by_kind
def test_save_invalid_data(client_logged, kind):
    data = {
        "date": "x",
        "price": "x",
        "from_account": 0,
        "to_account": 0,
    }

    response = client_logged.post(reverse(kind.new_url), data)
    actual = response.content.decode("utf-8")

    assert kind.model.objects.count() == 0
    assert actual.count('aria-invalid="true"') == 4


@pytest.mark.parametrize(
    "kind, kwargs, more",
    [
        pytest.param(
            KINDS["transactions"],
            {"price": 1},
            ('<option value="{to}">Account2</option>',),
            id="transactions",
        ),
        pytest.param(
            KINDS["savings_close"],
            {"price": 1, "fee": 1},
            ('name="fee" value="0.01"',),
            id="savings_close",
        ),
        pytest.param(
            KINDS["savings_change"],
            {"price": 1, "fee": 1},
            ('name="fee" value="0.01"', '<option value="{to}">Savings To</option>'),
            id="savings_change",
        ),
    ],
)
def test_load_update_form(client_logged, kind, kwargs, more):
    obj = kind.factory(**kwargs)

    url = reverse(kind.update_url, kwargs={"pk": obj.pk})
    response = client_logged.get(url)
    actual = clean_content(response.content.decode("utf-8"))

    assert "Atnaujinti ir uždaryti</button>" in actual
    assert url in actual
    assert f'<h5 class="modal-title">{kind.modal_title}</h5>' in actual
    assert 'name="date" value="1999-01-01"' in actual
    assert 'name="price" value="0.01"' in actual
    assert (
        f'<option value="{obj.from_account.pk}" selected>{kind.from_title}</option>'
        in actual
    )
    assert (
        f'<option value="{obj.to_account.pk}" selected>{kind.to_title}</option>'
        in actual
    )
    for snippet in more:
        assert snippet.format(to=obj.to_account.pk) in actual


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
@pytest.mark.parametrize(
    "url_name_of",
    [
        pytest.param(lambda kind: kind.update_url, id="update"),
        pytest.param(lambda kind: kind.delete_url, id="delete"),
    ],
)
def test_other_journal_form_not_found(client_logged, second_user, kind, url_name_of):
    obj = _foreign_move(kind, second_user.journal)

    url = reverse(url_name_of(kind), kwargs={"pk": obj.pk})
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
def test_delete_other_journal_post_form(client_logged, second_user, kind):
    obj = _foreign_move(kind, second_user.journal)

    url = reverse(kind.delete_url, kwargs={"pk": obj.pk})
    client_logged.post(url, follow=True)

    assert kind.model.objects.count() == 1


def _post_update(client_logged, kind, follow=False, **extra):
    obj = kind.factory()
    data = {
        "price": "0.01",
        "date": "1999-12-31",
        "from_account": obj.from_account.pk,
        "to_account": obj.to_account.pk,
    } | extra

    url = reverse(kind.update_url, kwargs={"pk": obj.pk})
    return client_logged.post(url, data, follow=follow)


def _assert_updated(actual, kind):
    assert actual.date == date(1999, 12, 31)
    assert actual.price == 1
    assert actual.to_account.title == kind.to_title
    assert actual.from_account.title == kind.from_title


@by_kind
def test_update(client_logged, kind):
    _post_update(client_logged, kind)

    _assert_updated(kind.model.objects.get(), kind)


@by_kind
def test_update_lands_on_its_list(client_logged, kind):
    response = _post_update(client_logged, kind, follow=True)
    page = response.content.decode("utf-8")

    assert "1999-12-31" in page
    assert kind.from_title in page
    assert kind.to_title in page


@by_fund_move
@pytest.mark.parametrize(
    "posted, cents",
    [pytest.param({"fee": "0.01"}, 1, id="fee"), pytest.param({}, 0, id="no_fee")],
)
def test_update_fee(client_logged, kind, posted, cents):
    _post_update(client_logged, kind, **posted)
    actual = kind.model.objects.get()

    _assert_updated(actual, kind)
    assert actual.fee == cents


def _new_url(kind):
    return reverse(kind.new_url)


def _closed_fund_update_url(kind, later_move=False):
    fund = SavingTypeFactory(closed=1999)
    obj = kind.factory(from_account=fund)
    if later_move:
        kind.factory(from_account=fund, date=date(1999, 6, 1))
    return reverse(kind.update_url, kwargs={"pk": obj.pk})


@by_fund_move
@pytest.mark.parametrize(
    "url_of, checked",
    [
        pytest.param(_new_url, 0, id="new"),
        pytest.param(_closed_fund_update_url, 1, id="update_of_a_closed_fund"),
        pytest.param(
            partial(_closed_fund_update_url, later_move=True),
            0,
            id="update_of_an_earlier_move",
        ),
    ],
)
@time_machine.travel("1999-1-1")
def test_close_checkbox_initial_value(client_logged, kind, url_of, checked):
    response = client_logged.get(url_of(kind))
    actual = response.content.decode("utf-8")

    assert len(CHECKED_BOX.findall(actual)) == checked


@by_fund_move
@pytest.mark.parametrize(
    "closed, close, expect",
    [
        pytest.param(1999, True, 1999, id="closed_stays_closed"),
        pytest.param(None, True, 1999, id="open_closes_in_the_moves_year"),
        pytest.param(1999, False, None, id="unticked_reopens"),
    ],
)
@time_machine.travel("2000-1-1")
def test_update_in_future_checkbox_value(client_logged, kind, closed, close, expect):
    a = SavingTypeFactory(closed=closed)
    obj = kind.factory(from_account=a)

    data = {
        "date": obj.date,
        "price": obj.price,
        "fee": obj.fee,
        "from_account": obj.from_account.pk,
        "to_account": obj.to_account.pk,
        "close": close,
    }

    url = reverse(kind.update_url, kwargs={"pk": obj.pk})
    client_logged.post(url, data)
    actual = SavingType.objects.get(pk=a.pk)

    # the fund closes in the move's year, not in the year it is edited
    assert actual.closed == expect


def _delete(client_logged, sell, other):
    client_logged.post(reverse("transactions:savings_close_delete", args=[sell.pk]))


def _move_to_another_fund(client_logged, sell, other):
    data = {
        "date": sell.date,
        "price": "15",
        "from_account": other.pk,
        "to_account": sell.to_account.pk,
    }
    url = reverse("transactions:savings_close_update", args=[sell.pk])
    client_logged.post(url, data)


# a partial sell before the closing one does not become the close
@pytest.mark.parametrize("edit", [_delete, _move_to_another_fund])
@time_machine.travel("2024-1-1")
def test_closing_sell_removed_reopens_the_fund(client_logged, edit):
    bank = AccountFactory(title="Bank")
    fund = SavingTypeFactory(title="Fund")
    other = SavingTypeFactory(title="Other")
    SavingFactory(account=bank, saving_type=fund, date=date(2020, 1, 1), price=1000)
    SavingCloseFactory(
        from_account=fund, to_account=bank, date=date(2021, 1, 1), price=100
    )
    SavingFactory(account=bank, saving_type=fund, date=date(2022, 1, 1), price=500)
    data = {
        "date": "2023-01-01",
        "price": "15",
        "from_account": fund.pk,
        "to_account": bank.pk,
        "close": "on",
    }
    client_logged.post(reverse("transactions:savings_close_new"), data)
    sell = models.SavingClose.objects.get(date=date(2023, 1, 1))
    assert SavingType.objects.get(pk=fund.pk).closed == 2023

    edit(client_logged, sell, other)

    assert SavingType.objects.get(pk=fund.pk).closed is None
    years = SavingBalance.objects.filter(saving_type=fund).values_list("year")
    assert {year for (year,) in years} >= {2020, 2021, 2022, 2023}


def test_savings_change_not_show_other_journal_types(client_logged, second_user):
    a_from = SavingTypeFactory()
    SavingTypeFactory(title="Own")
    SavingTypeFactory(title="XXX", journal=second_user.journal)

    data = {
        "date": "1999-01-01",
        "from_account": a_from.pk,
    }
    url = reverse("transactions:savings_change_new")
    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode("utf-8")

    assert actual.count(">Own</option>") == 2
    assert "XXX" not in actual


def test_load_saving_type_lists_the_open_funds_except_the_source(
    client_logged, second_user
):
    s1 = SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=1000)
    s3 = SavingTypeFactory(title="S3")
    SavingTypeFactory(title="S4", journal=second_user.journal)

    url = reverse("transactions:load_saving_type")
    response = client_logged.get(url, {"from_account": s1.pk})
    actual = response.content.decode("utf-8")

    assert "S1" not in actual
    assert "S2" not in actual
    assert "S4" not in actual
    assert f'<option value="{s3.pk}">S3</option>' in actual


@pytest.mark.parametrize(
    "data",
    [
        pytest.param({}, id="no-value"),
        pytest.param({"from_account": ""}, id="empty"),
        pytest.param({"from_account": "x"}, id="not-a-number"),
        pytest.param({"from_account": "0"}, id="zero"),
    ],
)
def test_load_saving_type_empty_parent_pk(client_logged, data):
    SavingTypeFactory(title="S1")

    url = reverse("transactions:load_saving_type")
    response = client_logged.get(url, data)

    assert response.status_code == 200
    assert "S1" not in response.content.decode("utf-8")


def test_load_saving_type_must_logged(client):
    url = reverse("transactions:load_saving_type")

    response = client.get(url, follow=True)

    assert response.status_code == 200
    assert response.resolver_match.func.view_class is Login


@pytest.mark.parametrize(
    "view_class",
    [views.Lists, views.SavingsCloseLists, views.SavingsChangeLists],
    ids=["transactions", "savings_close", "savings_change"],
)
def test_a_user_with_no_year_raises(rf, main_user, view_class):
    main_user.year = None

    with pytest.raises(ValueError, match="has no year"):
        view_for(rf, main_user, view_class).get_queryset()
