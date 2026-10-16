from datetime import date

import pytest

from ....accounts.tests.factories import AccountFactory
from ....users.tests.factories import UserFactory
from ... import forms
from .. import factories
from ..helpers import DEBT_FACTORIES, DEBT_TYPES, RETURN_FACTORIES

TODAY = date(2000, 2, 2)

pytestmark = pytest.mark.django_db


def test_debt_return_init_fields(main_user):
    form = forms.DebtReturnForm(user=main_user, today=TODAY, debt_type="lend").as_p()

    assert '<input type="text" name="date"' in form
    assert '<select name="account"' in form
    assert '<select name="debt"' in form
    assert '<input type="text" name="price"' in form
    assert '<textarea name="remark"' in form

    assert '<select name="user"' not in form


@pytest.mark.parametrize(
    "debt_type, label",
    [
        pytest.param("lend", "Paskolos gavėjas", id="lend"),
        pytest.param("borrow", "Paskolos davėjas", id="borrow"),
    ],
)
def test_debt_name_field_label(main_user, debt_type, label):
    form = forms.DebtReturnForm(user=main_user, today=TODAY, debt_type=debt_type).as_p()

    assert f'<label for="id_debt">{label}:</label>' in form


def test_debt_return_year_initial_value(main_user):
    UserFactory()

    form = forms.DebtReturnForm(
        user=main_user, today=date(2002, 2, 2), debt_type="lend"
    ).as_p()

    assert '<input type="text" name="date" value="1999-02-02"' in form


def test_debt_return_select_first_account(main_user, second_user):
    AccountFactory(title="A1", journal=second_user.journal)

    a2 = AccountFactory(title="A2")

    form = forms.DebtReturnForm(user=main_user, today=TODAY, debt_type="lend").as_p()

    expect = f'<option value="{a2.pk}" selected>{a2}</option>'
    assert expect in form


@pytest.mark.parametrize("debt_type", DEBT_TYPES)
@pytest.mark.parametrize(
    "price, cents",
    [
        pytest.param("0.01", 1, id="point"),
        pytest.param("12,1", 1210, id="decimal_comma"),
    ],
)
def test_debt_return_valid_data(main_user, debt_type, price, cents):
    a = AccountFactory()
    b = DEBT_FACTORIES[debt_type](price=200000)

    form = forms.DebtReturnForm(
        user=main_user,
        today=TODAY,
        debt_type=debt_type,
        data={
            "date": "1999-12-02",
            "debt": b.pk,
            "price": price,
            "account": a.pk,
            "remark": "Rm",
        },
    )

    assert form.is_valid(), form.errors

    e = form.save()
    assert e.date == date(1999, 12, 2)
    assert e.account == a
    assert e.debt == b
    assert e.price == cents
    assert e.remark == "Rm"


@pytest.mark.parametrize(
    "posted, errors",
    [
        pytest.param(
            "2000-03-01",
            {
                "date": [
                    "Data negali būti vėlesnė nei sąskaitos uždarymo data. "
                    "Sąskaita buvo uždaryta 1999."
                ]
            },
            id="after_closed",
        ),
        pytest.param("1999-12-31", {}, id="closed_year"),
    ],
)
def test_debt_return_date_after_the_account_closed(main_user, posted, errors):
    a = AccountFactory(closed=1999)
    b = factories.LendFactory(date=date(1999, 1, 1))

    form = forms.DebtReturnForm(
        user=main_user,
        today=TODAY,
        debt_type="lend",
        data={"date": posted, "debt": b.pk, "price": "1", "account": a.pk},
    )

    assert form.errors == errors


@pytest.mark.parametrize("year", [1998, 2001])
def test_debt_return_invalid_date(year, main_user):
    a = AccountFactory()
    b = factories.LendFactory()

    form = forms.DebtReturnForm(
        user=main_user,
        today=date(1999, 2, 2),
        debt_type="lend",
        data={
            "date": f"{year}-12-02",
            "debt": b.pk,
            "price": "1",
            "account": a.pk,
            "remark": "Rm",
        },
    )

    assert not form.is_valid()
    assert "date" in form.errors
    assert "Metai turi būti tarp 1999 ir 2000" in form.errors["date"]


def test_debt_return_blank_data(main_user):
    form = forms.DebtReturnForm(user=main_user, today=TODAY, debt_type="lend", data={})

    assert not form.is_valid()

    assert len(form.errors) == 4
    assert "date" in form.errors
    assert "debt" in form.errors
    assert "account" in form.errors
    assert "price" in form.errors


@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_debt_return_only_not_closed(main_user, debt_type):
    # both named: the assertions match substrings, and Faker can draw "Tim" inside
    # "Timothy" — a pass or fail that says nothing about what the form excluded
    closed = DEBT_FACTORIES[debt_type](name="Closed debt", closed=True)
    not_closed = DEBT_FACTORIES[debt_type](name="Open debt", closed=False)

    form = forms.DebtReturnForm(user=main_user, today=TODAY, debt_type=debt_type).as_p()

    assert closed.name not in form
    assert not_closed.name in form


@pytest.mark.parametrize("debt_type", DEBT_TYPES)
@pytest.mark.parametrize(
    "price, errors",
    [
        pytest.param("150", {"price": ["Mokėtina suma viršija skolą."]}, id="over"),
        pytest.param(
            "60.01", {"price": ["Mokėtina suma viršija skolą."]}, id="cent_over"
        ),
        pytest.param("60", {}, id="all_that_is_left"),
    ],
)
def test_debt_return_price_higher(main_user, debt_type, price, errors):
    a = AccountFactory()
    b = DEBT_FACTORIES[debt_type](price=10000)
    RETURN_FACTORIES[debt_type](debt=b, price=4000)

    form = forms.DebtReturnForm(
        user=main_user,
        today=TODAY,
        debt_type=debt_type,
        data={
            "date": "1999-1-1",
            "debt": b.pk,
            "price": price,
            "account": a.pk,
        },
    )

    assert form.errors == errors


@pytest.mark.parametrize(
    "day, errors",
    [
        pytest.param(
            "2000-12-31", {"date": ["Data yra ankstesnė nei skolos data."]}, id="before"
        ),
        pytest.param("2001-01-01", {}, id="the_debts_own_day"),
    ],
)
def test_debt_return_date_earlier(main_user, day, errors):
    a = AccountFactory()
    b = factories.LendFactory(date=date(2001, 1, 1))

    form = forms.DebtReturnForm(
        user=main_user,
        today=TODAY,
        debt_type="lend",
        data={
            "date": day,
            "debt": b.pk,
            "price": "1",
            "account": a.pk,
        },
    )

    assert form.errors == errors


@pytest.mark.parametrize("field", ["account", "debt"])
def test_debt_return_rejects_an_account_or_debt_of_another_journal(
    main_user, second_user, field
):
    data = {
        "date": "1999-12-02",
        "price": 0.01,
        "account": AccountFactory(title="Mine", journal=main_user.journal).pk,
        "debt": factories.LendFactory(journal=main_user.journal, price=200000).pk,
    }
    foreign = {
        "account": AccountFactory(title="Theirs", journal=second_user.journal),
        "debt": factories.LendFactory(journal=second_user.journal, price=200000),
    }
    data[field] = foreign[field].pk

    form = forms.DebtReturnForm(
        user=main_user, today=TODAY, debt_type="lend", data=data
    )

    assert not form.is_valid()
    assert field in form.errors
