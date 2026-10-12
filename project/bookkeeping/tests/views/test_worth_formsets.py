import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from ....accounts.tests.factories import AccountFactory
from ....pensions.tests.factories import PensionTypeFactory
from ....savings.tests.factories import SavingTypeFactory
from ...models import AccountWorth, PensionWorth, SavingWorth
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


def worth_post_queries(client, url, factory, fund_field, count, duplicate):
    funds = [factory(title=f"F{count}-{i}") for i in range(count)]
    rows = [{"date": "1999-9-9", "price": "5", fund_field: f.pk} for f in funds]
    if duplicate:
        rows[-1][fund_field] = funds[0].pk

    with CaptureQueriesContext(connection) as queries:
        client.post(reverse(url), post_data(rows))

    return len(queries)


@pytest.mark.django_db
@pytest.mark.parametrize("duplicate", [False, True], ids=["valid", "duplicate"])
@pytest.mark.parametrize(
    "url, factory, fund_field",
    [
        pytest.param(
            "bookkeeping:accounts_worth_new", AccountFactory, "account", id="account"
        ),
        pytest.param(
            "bookkeeping:savings_worth_new",
            SavingTypeFactory,
            "saving_type",
            id="saving_type",
        ),
        pytest.param(
            "bookkeeping:pensions_worth_new",
            PensionTypeFactory,
            "pension_type",
            id="pension",
        ),
    ],
)
def test_post_query_count_does_not_grow_with_the_rows(
    client_logged, url, factory, fund_field, duplicate
):
    two = worth_post_queries(client_logged, url, factory, fund_field, 2, duplicate)
    six = worth_post_queries(client_logged, url, factory, fund_field, 6, duplicate)

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
@pytest.mark.parametrize(
    "url, factory, fund_field, model",
    [
        pytest.param(
            "bookkeeping:accounts_worth_new",
            AccountFactory,
            "account",
            AccountWorth,
            id="account",
        ),
        pytest.param(
            "bookkeeping:savings_worth_new",
            SavingTypeFactory,
            "saving_type",
            SavingWorth,
            id="saving_type",
        ),
        pytest.param(
            "bookkeeping:pensions_worth_new",
            PensionTypeFactory,
            "pension_type",
            PensionWorth,
            id="pension",
        ),
    ],
)
def test_worth_form_rejects_a_fund_of_another_journal(
    client_logged, second_user, url, factory, fund_field, model
):
    foreign = factory(title="Foreign", journal=second_user.journal)
    data = post_data([{"date": "1999-2-3", "price": "0.01", fund_field: foreign.pk}])

    actual = client_logged.post(reverse(url), data).content.decode("utf-8")

    assert f'aria-describedby="id_form-0-{fund_field}_error"' in actual
    assert not model.objects.exists()


@pytest.mark.django_db
def test_modal_renders_the_formset_under_its_title_and_worth_css_class(client_logged):
    account = AccountFactory(title="A1")

    response = client_logged.get(reverse("bookkeeping:accounts_worth_new"))

    actual = response.content.decode("utf-8")
    assert "Sąskaitų vertė" in actual
    assert 'class="modal-body worth-form"' in actual
    assert f'<option value="{account.pk}" selected>A1</option>' in actual
