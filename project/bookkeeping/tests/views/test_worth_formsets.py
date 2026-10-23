import re
from datetime import UTC, datetime
from typing import NamedTuple

import pytest
import time_machine
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from ....accounts.tests.factories import AccountFactory
from ....core.tests.utils import PICKER_SCRIPT, setup_view
from ....pensions.tests.factories import PensionTypeFactory
from ....savings.tests.factories import SavingTypeFactory
from ... import views
from ...models import AccountWorth, PensionWorth, SavingWorth
from ..factories import (
    AccountWorthFactory,
    PensionWorthFactory,
    SavingWorthFactory,
)
from ..helper import post_data


@pytest.mark.django_db
@pytest.mark.parametrize(
    "count", [pytest.param(2, id="two"), pytest.param(6, id="six")]
)
def test_post_writes_all_rows_in_one_insert(client_logged, count):
    accounts = [AccountFactory(title=f"A{i}") for i in range(count)]
    rows = [{"date": "1999-9-9", "price": "5", "account": a.pk} for a in accounts]

    with CaptureQueriesContext(connection) as queries:
        client_logged.post(reverse("bookkeeping:accounts_worth_new"), post_data(rows))

    table = AccountWorth._meta.db_table
    inserts = [q for q in queries if q["sql"].startswith(f'INSERT INTO "{table}"')]
    assert len(inserts) == 1
    assert AccountWorth.objects.count() == count


class Worth(NamedTuple):
    url: str
    fund_factory: type
    worth_factory: type
    fund_field: str
    model: type


WORTH_FORMSETS = [
    pytest.param(
        Worth(
            "bookkeeping:accounts_worth_new",
            AccountFactory,
            AccountWorthFactory,
            "account",
            AccountWorth,
        ),
        id="account",
    ),
    pytest.param(
        Worth(
            "bookkeeping:savings_worth_new",
            SavingTypeFactory,
            SavingWorthFactory,
            "saving_type",
            SavingWorth,
        ),
        id="saving_type",
    ),
    pytest.param(
        Worth(
            "bookkeeping:pensions_worth_new",
            PensionTypeFactory,
            PensionWorthFactory,
            "pension_type",
            PensionWorth,
        ),
        id="pension",
    ),
]


def worth_post_queries(client, worth, count, duplicate):
    funds = [worth.fund_factory(title=f"F{count}-{i}") for i in range(count)]
    rows = [{"date": "1999-9-9", "price": "5", worth.fund_field: f.pk} for f in funds]
    if duplicate:
        rows[-1][worth.fund_field] = funds[0].pk

    with CaptureQueriesContext(connection) as queries:
        client.post(reverse(worth.url), post_data(rows))

    return len(queries)


@pytest.mark.django_db
@pytest.mark.parametrize("worth", WORTH_FORMSETS)
def test_post_stamps_the_time_of_day_in_utc(client_logged, worth):
    fund = worth.fund_factory()
    row = {"date": "1999-9-9", "price": "5", worth.fund_field: fund.pk}

    with time_machine.travel(datetime(1999, 1, 1, 13, 14, 15, tzinfo=UTC), tick=False):
        client_logged.post(reverse(worth.url), post_data([row]))

    assert worth.model.objects.get().date == datetime(
        1999, 9, 9, 13, 14, 15, tzinfo=UTC
    )


@pytest.mark.django_db
@pytest.mark.parametrize("duplicate", [False, True], ids=["valid", "duplicate"])
@pytest.mark.parametrize("worth", WORTH_FORMSETS)
def test_post_query_count_does_not_grow_with_the_rows(client_logged, worth, duplicate):
    two = worth_post_queries(client_logged, worth, 2, duplicate)
    six = worth_post_queries(client_logged, worth, 6, duplicate)

    assert two == six


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url, factory, closed_listed",
    [
        pytest.param(
            "bookkeeping:accounts_worth_new", AccountFactory, False, id="account"
        ),
        pytest.param(
            "bookkeeping:savings_worth_new", SavingTypeFactory, False, id="saving_type"
        ),
        pytest.param(
            "bookkeeping:pensions_worth_new", PensionTypeFactory, True, id="pension"
        ),
    ],
)
def test_worth_form_lists_the_users_funds(
    client_logged, main_user, second_user, url, factory, closed_listed
):
    factory(title="Open")
    factory(title="Closed", closed=main_user.year - 1)
    factory(title="Foreign", journal=second_user.journal)

    actual = client_logged.get(reverse(url)).content.decode("utf-8")

    assert ">Open</option>" in actual
    assert (">Closed</option>" in actual) is closed_listed
    assert ">Foreign</option>" not in actual


@pytest.mark.django_db
@pytest.mark.parametrize("worth", WORTH_FORMSETS)
def test_worth_form_rejects_a_fund_of_another_journal(
    client_logged, second_user, worth
):
    foreign = worth.fund_factory(title="Foreign", journal=second_user.journal)
    row = {"date": "1999-2-3", "price": "0.01", worth.fund_field: foreign.pk}

    actual = client_logged.post(reverse(worth.url), post_data([row]))

    error = f'aria-describedby="id_form-0-{worth.fund_field}_error"'
    assert error in actual.content.decode("utf-8")
    assert not worth.model.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("posted_id", ["foreign", "missing"])
@pytest.mark.parametrize("worth", WORTH_FORMSETS)
def test_worth_form_ignores_a_posted_row_id(
    client_logged, second_user, worth, posted_id
):
    foreign_fund = worth.fund_factory(title="Foreign", journal=second_user.journal)
    foreign = worth.worth_factory(price=5, **{worth.fund_field: foreign_fund})
    own = worth.fund_factory(title="Own")
    row_id = {"foreign": foreign.pk, "missing": foreign.pk + 1}[posted_id]
    row = {"id": row_id, "date": "1999-2-3", "price": "7", worth.fund_field: own.pk}

    with CaptureQueriesContext(connection) as queries:
        data = post_data([row]) | {"form-INITIAL_FORMS": 1}
        client_logged.post(reverse(worth.url), data)

    foreign.refresh_from_db()
    assert (getattr(foreign, worth.fund_field), foreign.price) == (foreign_fund, 5)
    own_rows = worth.model.objects.filter(**{worth.fund_field: own})
    assert list(own_rows.values_list("price", flat=True)) == [700]
    row_reads = f'SELECT "{worth.model._meta.db_table}"."id"'
    assert not [q for q in queries if q["sql"].startswith(row_reads)]


@pytest.mark.django_db
def test_modal_renders_the_formset_under_its_title_and_worth_css_class(client_logged):
    account = AccountFactory(title="A1")

    response = client_logged.get(reverse("bookkeeping:accounts_worth_new"))

    actual = response.content.decode("utf-8")
    assert "Sąskaitų vertė" in actual
    assert 'class="modal-body worth-form"' in actual
    assert f'<option value="{account.pk}" selected>A1</option>' in actual


@pytest.mark.django_db
@pytest.mark.parametrize(
    "send",
    [
        pytest.param(lambda client, url: client.get(url), id="get"),
        pytest.param(
            lambda client, url: client.post(
                url, post_data([{"date": "x", "price": "x", "account": 0}])
            ),
            id="invalid_post",
        ),
    ],
)
def test_worth_modal_loads_the_date_picker_once(client_logged, send):
    AccountFactory()

    response = send(client_logged, reverse("bookkeeping:accounts_worth_new"))

    actual = response.content.decode("utf-8")
    assert re.findall(PICKER_SCRIPT, actual) == ["date-picker.js"]


def worth_view(rf, main_user, view_class=views.AccountsWorthNew):
    rf.user = main_user
    return setup_view(view_class(), rf)


def unchanged_date(view):
    return view.get_formset_class()()["date"].value().strftime("%Y-%m-%d")


def bound_formset(view, rows, can_delete=False):
    formset_class = view.formset_class(extra=0)
    formset_class.can_delete = can_delete
    return formset_class(post_data(rows))


def posted_view(rf, main_user, rows):
    request = rf.post("/", post_data(rows))
    request.user = main_user
    return setup_view(views.AccountsWorthNew(), request)


@pytest.mark.django_db
def test_service_instance_is_built_once(rf, main_user):
    view = worth_view(rf, main_user)

    assert view.service_instance is view.service_instance


@pytest.mark.django_db
def test_unbound_formset_renders_one_form_per_fund_with_that_fund_selected(
    rf, main_user
):
    a1 = AccountFactory(title="A1")
    a2 = AccountFactory(title="A2")
    AccountWorthFactory(account=a1)
    view = worth_view(rf, main_user)

    actual = [str(form["account"]) for form in view.unbound_formset()]

    assert len(actual) == 2
    assert f'<option value="{a1.pk}" selected>A1</option>' in actual[0]
    assert f'<option value="{a2.pk}" selected>A2</option>' in actual[1]


@pytest.mark.django_db
def test_bound_formset_renders_only_the_posted_rows(rf, main_user):
    a1 = AccountFactory(title="A1")
    AccountFactory(title="A2")
    view = worth_view(rf, main_user)
    data = post_data([{"date": "1999-9-9", "price": "5", "account": a1.pk}])

    actual = [str(form["account"]) for form in view.bound_formset(data)]

    assert len(actual) == 1
    assert f'<option value="{a1.pk}" selected>A1</option>' in actual[0]


@pytest.mark.django_db
def test_post_with_invalid_formset_returns_the_formset_with_its_errors(rf, main_user):
    view = posted_view(rf, main_user, [{"date": "x", "price": "x", "account": 0}])

    response = view.post(view.request)

    formset = response.context_data["formset"]
    assert not formset.is_valid()
    assert set(formset.errors[0]) == {"date", "price", "account"}
    assert not AccountWorth.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "prices, saved",
    [
        pytest.param(
            [{"price": "100"}, {"price": ""}],
            [("A1", 10000, "1999-09-09")],
            id="some_priced",
        ),
        pytest.param([{"price": ""}, {}], [], id="none_priced"),
    ],
)
def test_post_saves_only_the_rows_with_a_price(rf, main_user, prices, saved):
    funds = [AccountFactory(title="A1"), AccountFactory(title="A2")]
    rows = [
        {"date": "1999-9-9", "account": fund.pk} | price
        for fund, price in zip(funds, prices, strict=True)
    ]
    view = posted_view(rf, main_user, rows)

    response = view.post(view.request)

    actual = AccountWorth.objects.all()
    assert [
        (w.account.title, w.price, w.date.strftime("%Y-%m-%d")) for w in actual
    ] == saved
    assert response.status_code == 204
    assert response["HX-Trigger"] == '{"afterAccountWorthNew": {}}'


@pytest.mark.django_db
def test_post_syncs_the_balances_of_the_saved_rows_user(rf, main_user, mocker):
    a1 = AccountFactory(title="A1")
    view = posted_view(
        rf, main_user, [{"date": "1999-9-9", "price": "100", "account": a1.pk}]
    )
    mock_sync = mocker.patch.object(views.AccountsWorthNew, "balance_sync")

    view.post(view.request)

    mock_sync.assert_called_once_with(main_user)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "view_class, factory, fund_field, message",
    [
        pytest.param(
            views.AccountsWorthNew,
            AccountFactory,
            "account",
            "Pasirinktos vienodos sąskaitos.",
            id="account",
        ),
        pytest.param(
            views.SavingsWorthNew,
            SavingTypeFactory,
            "saving_type",
            "Pasirinkti vienodi fondai.",
            id="saving_type",
        ),
        pytest.param(
            views.PensionsWorthNew,
            PensionTypeFactory,
            "pension_type",
            "Pasirinktos vienodos pensijos.",
            id="pension",
        ),
    ],
)
@pytest.mark.parametrize("copies", [2, 3])
def test_clean_tags_the_fund_field_the_model_names(
    rf, main_user, view_class, factory, fund_field, message, copies
):
    fund = factory()
    view = worth_view(rf, main_user, view_class)
    row = {"date": "1999-9-9", "price": "5", fund_field: fund.pk}

    actual = bound_formset(view, [row] * copies)

    assert not actual.is_valid()
    assert [form.errors for form in actual.forms] == [{fund_field: [message]}] * copies


@pytest.mark.django_db
def test_clean_does_not_tag_duplicates_when_a_form_already_has_errors(rf, main_user):
    row = {"date": "1999-9-9", "price": "5", "account": AccountFactory().pk}
    view = worth_view(rf, main_user)

    actual = bound_formset(view, [row, row, row | {"price": "x"}])

    assert not actual.is_valid()
    assert [set(form.errors) for form in actual.forms] == [set(), set(), {"price"}]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "rows",
    [
        pytest.param(["empty"], id="empty"),
        pytest.param(["filled", "deleted"], id="deleted"),
        pytest.param(["blank", "blank"], id="blank"),
    ],
)
def test_clean_skips_a_form_that_is_empty_deleted_or_blank(rf, main_user, rows):
    account = AccountFactory()
    view = worth_view(rf, main_user)

    class BlankAllowedForm(view.form_class):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["account"].required = False

    view.form_class = BlankAllowedForm
    date = unchanged_date(view)
    filled = {"date": date, "price": "5", "account": account.pk}
    posted = {
        "empty": {"date": date},
        "filled": filled,
        "deleted": filled | {"DELETE": "on"},
        "blank": {"date": date, "price": "5", "account": ""},
    }

    actual = bound_formset(view, [posted[row] for row in rows], can_delete=True)

    assert actual.is_valid()
    assert [form.errors for form in actual.forms] == [{}] * len(rows)
