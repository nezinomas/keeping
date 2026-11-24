import re
from datetime import UTC, datetime
from typing import NamedTuple

import pytest
import time_machine
from django.urls import reverse

from ....accounts.models import AccountBalance
from ....accounts.tests.factories import AccountFactory
from ....core.tests.utils import PICKER_SCRIPT, count_queries, setup_view
from ....pensions.models import PensionBalance
from ....pensions.tests.factories import PensionTypeFactory
from ....savings.models import SavingBalance
from ....savings.tests.factories import SavingTypeFactory
from ... import views
from ...models import AccountWorth, PensionWorth, SavingWorth
from ..factories import (
    AccountWorthFactory,
    PensionWorthFactory,
    SavingWorthFactory,
)
from ..helper import post_data, quiet_syncs


@pytest.mark.django_db
@pytest.mark.parametrize(
    "count", [pytest.param(2, id="two"), pytest.param(6, id="six")]
)
def test_post_writes_all_rows_in_one_insert(client_logged, count):
    accounts = [AccountFactory(title=f"A{i}") for i in range(count)]
    rows = [{"date": "1999-9-9", "price": "5", "account": a.pk} for a in accounts]

    inserts = count_queries(
        lambda: client_logged.post(
            reverse("bookkeeping:accounts_worth_new"), post_data(rows)
        ),
        starting_with=f'INSERT INTO "{AccountWorth._meta.db_table}"',
    )

    assert inserts == 1
    assert AccountWorth.objects.count() == count


class Worth(NamedTuple):
    url: str
    view: type
    owner_factory: type
    worth_factory: type
    owner_field: str
    model: type
    title: str
    duplicate_message: str
    balance: type
    balance_field: str
    closed_listed: bool


WORTH_FORMSETS = [
    pytest.param(
        Worth(
            url="bookkeeping:accounts_worth_new",
            view=views.AccountsWorthNew,
            owner_factory=AccountFactory,
            worth_factory=AccountWorthFactory,
            owner_field="account",
            model=AccountWorth,
            title="Sąskaitų vertė",
            duplicate_message="Pasirinktos vienodos sąskaitos.",
            balance=AccountBalance,
            balance_field="have",
            closed_listed=False,
        ),
        id="account",
    ),
    pytest.param(
        Worth(
            url="bookkeeping:savings_worth_new",
            view=views.SavingsWorthNew,
            owner_factory=SavingTypeFactory,
            worth_factory=SavingWorthFactory,
            owner_field="saving_type",
            model=SavingWorth,
            title="Fondų vertė",
            duplicate_message="Pasirinkti vienodi fondai.",
            balance=SavingBalance,
            balance_field="market_value",
            closed_listed=False,
        ),
        id="saving_type",
    ),
    pytest.param(
        Worth(
            url="bookkeeping:pensions_worth_new",
            view=views.PensionsWorthNew,
            owner_factory=PensionTypeFactory,
            worth_factory=PensionWorthFactory,
            owner_field="pension_type",
            model=PensionWorth,
            title="Pensijų vertė",
            duplicate_message="Pasirinktos vienodos pensijos.",
            balance=PensionBalance,
            balance_field="market_value",
            closed_listed=True,
        ),
        id="pension",
    ),
]


def worth_post_queries(client, worth, count, duplicate):
    with quiet_syncs():
        owners = [worth.owner_factory(title=f"F{count}-{i}") for i in range(count)]
    rows = [{"date": "1999-9-9", "price": "5", worth.owner_field: f.pk} for f in owners]
    if duplicate:
        rows[-1][worth.owner_field] = owners[0].pk

    return count_queries(lambda: client.post(reverse(worth.url), post_data(rows)))


@pytest.mark.django_db
@pytest.mark.parametrize("worth", WORTH_FORMSETS)
def test_post_stamps_the_time_of_day_in_utc(client_logged, worth):
    owner = worth.owner_factory()
    row = {"date": "1999-9-9", "price": "5", worth.owner_field: owner.pk}

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
    four = worth_post_queries(client_logged, worth, 4, duplicate)

    assert two == four


@pytest.mark.django_db
@pytest.mark.parametrize("worth", WORTH_FORMSETS)
def test_worth_form_lists_the_users_owners(
    client_logged, main_user, second_user, worth
):
    worth.owner_factory(title="Open")
    worth.owner_factory(title="Closed", closed=main_user.year - 1)
    worth.owner_factory(title="Foreign", journal=second_user.journal)

    actual = client_logged.get(reverse(worth.url)).content.decode("utf-8")

    assert ">Open</option>" in actual
    assert (">Closed</option>" in actual) is worth.closed_listed
    assert ">Foreign</option>" not in actual


@pytest.mark.django_db
@pytest.mark.parametrize("worth", WORTH_FORMSETS)
def test_worth_form_rejects_an_owner_of_another_journal(
    client_logged, second_user, worth
):
    foreign = worth.owner_factory(title="Foreign", journal=second_user.journal)
    row = {"date": "1999-2-3", "price": "0.01", worth.owner_field: foreign.pk}

    actual = client_logged.post(reverse(worth.url), post_data([row]))

    error = f'aria-describedby="id_form-0-{worth.owner_field}_error"'
    assert error in actual.content.decode("utf-8")
    assert not worth.model.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("posted_id", ["foreign", "missing"])
@pytest.mark.parametrize("worth", WORTH_FORMSETS)
def test_worth_form_ignores_a_posted_row_id(
    client_logged, second_user, worth, posted_id
):
    foreign_owner = worth.owner_factory(title="Foreign", journal=second_user.journal)
    foreign = worth.worth_factory(price=5, **{worth.owner_field: foreign_owner})
    own = worth.owner_factory(title="Own")
    row_id = {"foreign": foreign.pk, "missing": foreign.pk + 1}[posted_id]
    row = {"id": row_id, "date": "1999-2-3", "price": "7", worth.owner_field: own.pk}

    data = post_data([row]) | {"form-INITIAL_FORMS": 1}

    row_reads = count_queries(
        lambda: client_logged.post(reverse(worth.url), data),
        starting_with=f'SELECT "{worth.model._meta.db_table}"."id"',
    )

    foreign.refresh_from_db()
    assert (getattr(foreign, worth.owner_field), foreign.price) == (foreign_owner, 5)
    own_rows = worth.model.objects.filter(**{worth.owner_field: own})
    assert list(own_rows.values_list("price", flat=True)) == [700]
    assert row_reads == 0


@pytest.mark.django_db
@pytest.mark.parametrize("worth", WORTH_FORMSETS)
def test_modal_renders_the_formset_under_its_title_and_worth_css_class(
    client_logged, worth
):
    owner = worth.owner_factory(title="F1")

    response = client_logged.get(reverse(worth.url))

    actual = response.content.decode("utf-8")
    assert f'<h5 class="modal-title">{worth.title}</h5>' in actual
    assert 'class="modal-body worth-form"' in actual
    assert f'<option value="{owner.pk}" selected>F1</option>' in actual


@pytest.mark.django_db
@pytest.mark.parametrize("worth", WORTH_FORMSETS)
def test_modal_has_one_unpriced_form_per_owner_with_that_owner_selected(
    client_logged, worth
):
    f1 = worth.owner_factory(title="F1")
    f2 = worth.owner_factory(title="F2")
    worth.worth_factory(**{worth.owner_field: f1})

    content = client_logged.get(reverse(worth.url)).content.decode()

    selected = re.findall(r'<option value="(\d+)" selected>([^<]*)</option>', content)
    prices = re.findall(r'<input[^>]*name="form-\d+-price"[^>]*>', content)
    assert selected == [(str(f1.pk), "F1"), (str(f2.pk), "F2")]
    assert ["value=" in price for price in prices] == [False, False]


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
def test_bound_formset_renders_only_the_posted_rows(rf, main_user):
    a1 = AccountFactory(title="A1")
    AccountFactory(title="A2")
    view = worth_view(rf, main_user)
    data = post_data([{"date": "1999-9-9", "price": "5", "account": a1.pk}])

    actual = [str(form["account"]) for form in view.bound_formset(data)]

    assert len(actual) == 1
    assert f'<option value="{a1.pk}" selected>A1</option>' in actual[0]


@pytest.mark.django_db
def test_post_with_invalid_formset_returns_the_formset_with_its_errors(client_logged):
    row = {"date": "x", "price": "x", "account": 0}

    response = client_logged.post(
        reverse("bookkeeping:accounts_worth_new"), post_data([row])
    )

    actual = re.findall(
        r'aria-describedby="id_form-0-(\w+)_error"', response.content.decode("utf-8")
    )
    assert sorted(actual) == ["account", "date", "price"]
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
        pytest.param(
            [{"price": "0"}, {"price": ""}],
            [("A1", 0, "1999-09-09")],
            id="zero_priced",
        ),
        pytest.param([{"price": ""}, {}], [], id="none_priced"),
    ],
)
def test_post_saves_only_the_rows_with_a_price(rf, main_user, prices, saved):
    owners = [AccountFactory(title="A1"), AccountFactory(title="A2")]
    rows = [
        {"date": "1999-9-9", "account": owner.pk} | price
        for owner, price in zip(owners, prices, strict=True)
    ]
    view = posted_view(rf, main_user, rows)

    response = view.post(view.request)

    actual = AccountWorth.objects.all()
    assert [
        (w.account.title, w.price, w.date.strftime("%Y-%m-%d")) for w in actual
    ] == saved
    assert response.status_code == 204


@pytest.mark.django_db
@pytest.mark.parametrize("worth", WORTH_FORMSETS)
def test_post_syncs_the_balances_of_the_saved_rows_user_and_reloads_the_tab(
    client_logged, worth
):
    owner = worth.owner_factory()
    row = {"date": "1999-9-9", "price": "0.01", worth.owner_field: owner.pk}

    response = client_logged.post(reverse(worth.url), post_data([row]))

    actual = worth.balance.objects.values_list("year", worth.balance_field)
    assert list(actual) == [(1999, 1), (2000, 1)]
    assert response["HX-Trigger"] == '{"reload": {}}'


@pytest.mark.django_db
@pytest.mark.parametrize("worth", WORTH_FORMSETS)
def test_clean_tags_the_owner_field_the_model_names(rf, main_user, worth):
    owner = worth.owner_factory()
    view = worth_view(rf, main_user, worth.view)
    row = {"date": "1999-9-9", "price": "5", worth.owner_field: owner.pk}

    actual = bound_formset(view, [row] * 3)

    assert not actual.is_valid()
    expected = [{worth.owner_field: [worth.duplicate_message]}] * 3
    assert [form.errors for form in actual.forms] == expected


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
