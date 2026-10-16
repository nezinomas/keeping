from datetime import date

import pytest

from ...accounts.tests.factories import AccountFactory
from ...journals.tests.factories import JournalFactory
from ...users.tests.factories import UserFactory
from ..forms import SavingForm, SavingTypeForm
from ..models import SavingType
from .factories import SavingTypeFactory

pytestmark = pytest.mark.django_db

TODAY = date(1999, 1, 1)


def test_saving_type_init(main_user):
    form = SavingTypeForm(user=main_user, today=TODAY)

    assert form.fields["journal"].initial == main_user.journal
    assert form.fields["journal"].disabled


def test_saving_type_init_fields(main_user):
    form = SavingTypeForm(user=main_user, today=TODAY).as_p()

    assert '<input type="text" name="title"' in form
    assert '<input type="text" name="closed"' in form
    assert '<select name="user"' not in form


@pytest.mark.parametrize(
    "closed",
    [
        ("2000"),
        (2000),
    ],
)
def test_saving_type_valid_data(main_user, closed):
    form = SavingTypeForm(
        user=main_user,
        today=TODAY,
        data={
            "title": "Title",
            "closed": closed,
            "type": "funds",
            "fee_source": "investment",
        },
    )

    assert form.is_valid()

    data = form.save()

    assert data.title == "Title"
    assert data.closed == 2000
    assert data.journal.title == "bob Journal"
    assert data.journal.users.first().username == "bob"


@pytest.mark.parametrize("closed", [1999, None])
def test_saving_type_with_no_close_year_saves_open(main_user, closed):
    fund = SavingTypeFactory(closed=closed)
    form = SavingTypeForm(
        user=main_user,
        today=TODAY,
        instance=fund,
        data={
            "title": "Title",
            "closed": "",
            "type": "funds",
            "fee_source": "investment",
        },
    )

    assert form.is_valid()
    assert form.save().closed is None


def test_saving_type_fee_source_field(main_user):
    form = SavingTypeForm(user=main_user, today=TODAY).as_p()

    assert '<select name="fee_source"' in form
    assert "Mokestis nuskaitomas" in form
    assert '<option value="investment" selected>iš investicijos</option>' in form
    assert '<option value="account">iš sąskaitos</option>' in form


@pytest.mark.parametrize("fee_source", ["investment", "account"])
def test_saving_type_saves_fee_source(main_user, fee_source):
    form = SavingTypeForm(
        user=main_user,
        today=TODAY,
        data={"title": "Title", "type": "funds", "fee_source": fee_source},
    )

    assert form.is_valid()
    assert form.save().fee_source == fee_source


def test_saving_type_rejects_unknown_fee_source(main_user):
    form = SavingTypeForm(
        user=main_user,
        today=TODAY,
        data={"title": "Title", "type": "funds", "fee_source": "bank"},
    )

    assert not form.is_valid()
    assert "fee_source" in form.errors


def test_saving_type_blank_data(main_user):
    form = SavingTypeForm(user=main_user, today=TODAY, data={})

    assert not form.is_valid()

    assert len(form.errors) == 3
    assert "title" in form.errors
    assert "type" in form.errors
    assert "fee_source" in form.errors


@pytest.mark.parametrize(
    "title",
    [None, "aa", "a" * 255],
    ids=["null", "too_short", "too_long"],
)
def test_saving_type_title_rejected(main_user, title):
    form = SavingTypeForm(user=main_user, today=TODAY, data={"title": title})

    assert not form.is_valid()

    assert "title" in form.errors


def test_saving_type_title_max_symbols(main_user):
    title = "a" * 50
    form = SavingTypeForm(
        user=main_user,
        today=TODAY,
        data={
            "title": title,
            "journal": JournalFactory(),
            "type": "funds",
            "fee_source": "investment",
        },
    )

    assert form.is_valid()

    form.save()

    assert SavingType.objects.first().title == title


@pytest.mark.parametrize(
    "user_year, closed_listed",
    [(3000, False), (1000, True), (2000, True)],
    ids=["after_closed", "before_closed", "closed_year"],
)
def test_saving_type_closed(main_user, user_year, closed_listed):
    main_user.year = user_year
    main_user.save()

    SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=2000)

    form = SavingForm(user=main_user, today=TODAY, data={})

    assert "S1" in str(form["saving_type"])
    assert ("S2" in str(form["saving_type"])) is closed_listed


@pytest.mark.parametrize(
    "existing, title, message",
    [
        pytest.param("Finbee", "Finbee", "„Finbee“ jau yra.", id="title_taken"),
        pytest.param(
            "Būstas",
            "Bustas",
            "Pavadinimas per daug panašus į jau esantį „Būstas“.",
            id="slug_taken",
        ),
    ],
)
def test_saving_type_title_taken(main_user, existing, title, message):
    SavingType.objects.create(title=existing, journal=main_user.journal)

    form = SavingTypeForm(
        user=main_user, today=TODAY, data={"title": title, "type": "funds"}
    )

    assert not form.is_valid()

    assert form.errors["title"] == [message]


def test_saving_type_title_taken_in_other_journal(main_user, second_user):
    SavingType.objects.create(title="Finbee", journal=second_user.journal)

    form = SavingTypeForm(
        user=main_user,
        today=TODAY,
        data={"title": "Finbee", "type": "funds", "fee_source": "investment"},
    )

    assert form.is_valid()


def test_saving_type_edit_keeps_own_title(main_user):
    obj = SavingType.objects.create(title="Finbee", journal=main_user.journal)

    form = SavingTypeForm(
        user=main_user,
        today=TODAY,
        instance=obj,
        data={"title": "Finbee", "type": "funds", "fee_source": "investment"},
    )

    assert form.is_valid()


def test_saving_type_title_without_character_rule(main_user):
    form = SavingTypeForm(
        user=main_user,
        today=TODAY,
        data={
            "title": "Artea Ambicingas Index 16+",
            "type": "funds",
            "fee_source": "investment",
        },
    )

    assert form.is_valid()


@pytest.mark.parametrize(
    "title, message",
    [
        ("Fondas ½", "Pavadinime negali būti „½“."),
        ("€€€", "Pavadinime turi būti bent viena lotyniška raidė arba skaitmuo."),
    ],
)
def test_saving_type_title_slug_rules(main_user, title, message):
    form = SavingTypeForm(
        user=main_user, today=TODAY, data={"title": title, "type": "funds"}
    )

    assert not form.is_valid()

    assert form.errors["title"] == [message]


def test_saving_year_initial_value(main_user):
    UserFactory()

    form = SavingForm(user=main_user, today=TODAY).as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form


def test_saving_select_first_account(main_user, second_user):
    AccountFactory(title="S1", journal=second_user.journal)
    s2 = AccountFactory(title="S2")

    form = SavingForm(user=main_user, today=TODAY).as_p()

    expect = f'<option value="{s2.pk}" selected>{s2}</option>'
    assert expect in form


def test_saving_valid_data(main_user):
    a = AccountFactory()
    t = SavingTypeFactory()

    form = SavingForm(
        user=main_user,
        today=TODAY,
        data={
            "date": "1999-01-01",
            "price": 0.01,
            "fee": 0.01,
            "remark": "remark",
            "account": a.pk,
            "saving_type": t.pk,
        },
    )

    assert form.is_valid()

    data = form.save()

    assert data.date == date(1999, 1, 1)
    assert data.price == 1
    assert data.fee == 1
    assert data.remark == "remark"
    assert data.account.title == a.title
    assert data.saving_type.title == t.title


@pytest.mark.parametrize(
    "price",
    [
        (""),
        (None),
        (0),
    ],
)
def test_saving_valid_data_only_fee(main_user, price):
    a = AccountFactory()
    t = SavingTypeFactory()

    form = SavingForm(
        user=main_user,
        today=TODAY,
        data={
            "date": "1999-01-01",
            "price": price,
            "fee": 0.01,
            "remark": "remark",
            "account": a.pk,
            "saving_type": t.pk,
        },
    )

    assert form.is_valid()

    data = form.save()

    assert data.date == date(1999, 1, 1)
    assert not data.price
    assert data.fee == 1
    assert data.remark == "remark"
    assert data.account.title == a.title
    assert data.saving_type.title == t.title


def test_saving_valid_data_with_no_fee(main_user):
    a = AccountFactory()
    t = SavingTypeFactory()

    form = SavingForm(
        user=main_user,
        today=TODAY,
        data={
            "date": "1999-01-01",
            "price": 0.01,
            "remark": "remark",
            "account": a.pk,
            "saving_type": t.pk,
        },
    )

    assert form.is_valid()

    data = form.save()

    assert data.date == date(1999, 1, 1)
    assert data.price == 1
    assert not data.fee
    assert data.remark == "remark"
    assert data.account.title == a.title
    assert data.saving_type.title == t.title


@pytest.mark.parametrize("empty", ["", None])
def test_saving_empty_fee_saves_zero(main_user, empty):
    form = SavingForm(
        user=main_user,
        today=TODAY,
        data={
            "date": "1999-01-01",
            "price": 0.01,
            "fee": empty,
            "account": AccountFactory().pk,
            "saving_type": SavingTypeFactory().pk,
        },
    )

    assert form.is_valid()

    actual = form.save()

    actual.refresh_from_db()
    assert actual.price == 1
    assert actual.fee == 0


@pytest.mark.parametrize("empty", ["", None])
def test_saving_empty_price_beside_a_fee_saves_zero(main_user, empty):
    form = SavingForm(
        user=main_user,
        today=TODAY,
        data={
            "date": "1999-01-01",
            "price": empty,
            "fee": 0.01,
            "account": AccountFactory().pk,
            "saving_type": SavingTypeFactory().pk,
        },
    )

    assert form.is_valid()

    actual = form.save()

    actual.refresh_from_db()
    assert actual.price == 0
    assert actual.fee == 1


def test_saving_price_and_fee_accept_a_decimal_comma(main_user):
    a = AccountFactory()
    t = SavingTypeFactory()

    form = SavingForm(
        user=main_user,
        today=TODAY,
        data={
            "date": "1999-01-01",
            "price": "12,1",
            "fee": "0,55",
            "account": a.pk,
            "saving_type": t.pk,
        },
    )

    assert form.is_valid(), form.errors

    data = form.save()

    assert data.price == 1210
    assert data.fee == 55


@pytest.mark.parametrize("year", [1998, 2001])
def test_saving_invalid_date(main_user, year):
    a = AccountFactory()
    t = SavingTypeFactory()

    form = SavingForm(
        user=main_user,
        today=TODAY,
        data={
            "date": f"{year}-01-01",
            "price": "10",
            "fee": "2",
            "remark": "remark",
            "account": a.pk,
            "saving_type": t.pk,
        },
    )

    assert not form.is_valid()
    assert "date" in form.errors
    assert "Metai turi būti tarp 1999 ir 2000" in form.errors["date"]


@pytest.mark.parametrize(
    "posted, errors",
    [
        pytest.param(
            "2000-01-01", {"date": ["Fondas uždarytas 1999."]}, id="after_closed"
        ),
        pytest.param("1999-12-31", {}, id="closed_year"),
        pytest.param("1998-12-31", {}, id="before_closed"),
    ],
)
def test_saving_date_after_the_fund_closed(main_user, posted, errors):
    main_user.journal.first_record = date(1998, 1, 1)
    main_user.journal.save()
    a = AccountFactory()
    t = SavingTypeFactory(closed=1999)

    form = SavingForm(
        user=main_user,
        today=TODAY,
        data={
            "date": posted,
            "price": "10",
            "account": a.pk,
            "saving_type": t.pk,
        },
    )

    assert form.errors == errors


def test_saving_blank_data(main_user):
    form = SavingForm(user=main_user, today=TODAY, data={})

    assert not form.is_valid()

    assert "date" in form.errors
    assert "price" in form.errors
    assert "account" in form.errors
    assert "saving_type" in form.errors


def test_saving_price_null_and_fee_null(main_user):
    a = AccountFactory()
    t = SavingTypeFactory()

    form = SavingForm(
        user=main_user,
        today=TODAY,
        data={
            "date": "2000-01-01",
            "price": "",
            "fee": "",
            "remark": "remark",
            "account": a.pk,
            "saving_type": t.pk,
        },
    )

    assert not form.is_valid()
    assert "price" in form.errors


def _saving_type_data(second_user, title):
    return {
        "journal": second_user.journal.pk,
        "title": title,
        "closed": "",
        "type": "funds",
        "fee_source": "investment",
    }


@pytest.mark.parametrize("editing", [False, True], ids=["create", "edit"])
def test_saving_type_ignores_a_posted_journal(main_user, second_user, editing):
    obj = (
        SavingTypeFactory(title="Mine", journal=main_user.journal) if editing else None
    )

    form = SavingTypeForm(
        user=main_user,
        today=TODAY,
        instance=obj,
        data=_saving_type_data(second_user, "Mine"),
    )

    assert form.is_valid()

    assert form.save().journal == main_user.journal


@pytest.mark.parametrize("field", ["account", "saving_type"])
def test_saving_rejects_a_fund_or_account_of_another_journal(
    main_user, second_user, field
):
    data = {
        "date": "1999-01-01",
        "price": 0.01,
        "account": AccountFactory(title="Mine", journal=main_user.journal).pk,
        "saving_type": SavingTypeFactory(title="Mine", journal=main_user.journal).pk,
    }
    foreign = {
        "account": AccountFactory(title="Theirs", journal=second_user.journal),
        "saving_type": SavingTypeFactory(title="Theirs", journal=second_user.journal),
    }
    data[field] = foreign[field].pk

    form = SavingForm(user=main_user, today=TODAY, data=data)

    assert not form.is_valid()
    assert field in form.errors
