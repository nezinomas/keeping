from datetime import UTC, date, datetime

import pytest

from ...accounts.tests.factories import AccountFactory
from ...bookkeeping.tests.factories import SavingWorthFactory
from ...bookkeeping.tests.helper import quiet_build
from ...core.tests.utils import count_queries
from ...journals.tests.factories import JournalFactory
from ...plans.tests.factories import SavingPlanFactory
from ...transactions.tests.factories import SavingChangeFactory, SavingCloseFactory
from ..forms import SavingForm, SavingTypeForm
from ..models import SavingType
from .factories import SavingFactory, SavingTypeFactory

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
    ("field", "label"),
    [
        ("title", "Fondas"),
        ("closed", "Uždaryta"),
        ("type", "Tipas"),
        ("fee_source", "Mokestis nuskaitomas"),
    ],
)
def test_saving_type_form_labels(main_user, field, label):
    form = SavingTypeForm(user=main_user, today=TODAY)

    assert form[field].label == label


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


FUND_ROWS = {
    "buy": lambda fund, year: SavingFactory(saving_type=fund, date=date(year, 6, 1)),
    "sell": lambda fund, year: SavingCloseFactory(
        from_account=fund, date=date(year, 6, 1)
    ),
    "switch_out": lambda fund, year: SavingChangeFactory(
        from_account=fund, date=date(year, 6, 1)
    ),
    "switch_in": lambda fund, year: SavingChangeFactory(
        to_account=fund, date=date(year, 6, 1)
    ),
    "worth": lambda fund, year: SavingWorthFactory(
        saving_type=fund,
        date=datetime(year, 6, 1, tzinfo=UTC),
    ),
    "plan": lambda fund, year: SavingPlanFactory(saving_type=fund, year=year),
}


def _fund_form(user, fund, closed):
    return SavingTypeForm(
        user=user,
        today=TODAY,
        instance=fund,
        data={
            "title": fund.title,
            "closed": closed,
            "type": "funds",
            "fee_source": "investment",
        },
    )


@pytest.mark.parametrize("row", FUND_ROWS)
@pytest.mark.parametrize(
    "closed, errors",
    [
        (
            "2000",
            {"closed": ["Negalima uždaryti anksčiau nei 2001: tais metais yra įrašų."]},
        ),
        ("2001", {}),
        ("2005", {}),
        ("", {}),
    ],
)
def test_saving_type_close_year_not_before_its_rows(main_user, row, closed, errors):
    fund = SavingTypeFactory()
    FUND_ROWS[row](fund, 1999)
    FUND_ROWS[row](fund, 2001)

    assert _fund_form(main_user, fund, closed).errors == errors


def test_saving_type_close_year_query_count(main_user):
    def queries(fund, rows):
        with quiet_build(main_user):
            for year in range(1999, 1999 + rows):
                for make in FUND_ROWS.values():
                    make(fund, year)
        form = _fund_form(main_user, fund, "2010")
        return count_queries(form.is_valid)

    assert queries(SavingTypeFactory(title="F2"), 2) == queries(
        SavingTypeFactory(title="F6"), 6
    )


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
    form = SavingForm(user=main_user, today=date(1974, 1, 1)).as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form


def test_saving_form_widgets(main_user):
    form = SavingForm(user=main_user, today=TODAY)

    assert form["date"].widget_type == "datepicker"
    assert form["remark"].field.widget.attrs["rows"] == 3


@pytest.mark.parametrize(
    ("field", "label"),
    [
        ("date", "Data"),
        ("account", "Iš sąskaitos"),
        ("price", "Suma"),
        ("fee", "Mokesčiai"),
        ("remark", "Pastaba"),
        ("saving_type", "Fondas"),
    ],
)
def test_saving_form_labels(main_user, field, label):
    form = SavingForm(user=main_user, today=TODAY)

    assert form[field].label == label


def test_saving_select_first_account(main_user, second_user):
    AccountFactory(title="S1", journal=second_user.journal)
    s2 = AccountFactory(title="S2")

    form = SavingForm(user=main_user, today=TODAY).as_p()

    expect = f'<option value="{s2.pk}" selected>{s2}</option>'
    assert expect in form


@pytest.mark.parametrize(
    "amounts, expect_price, expect_fee",
    [
        pytest.param({"price": 0.01, "fee": 0.01}, 1, 1, id="price_and_fee"),
        pytest.param({"price": "", "fee": 0.01}, 0, 1, id="only_fee_empty_price"),
        pytest.param({"price": None, "fee": 0.01}, 0, 1, id="only_fee_none_price"),
        pytest.param({"price": 0, "fee": 0.01}, 0, 1, id="only_fee_zero_price"),
        pytest.param({"price": 0.01}, 1, 0, id="no_fee"),
    ],
)
def test_saving_valid_data(main_user, amounts, expect_price, expect_fee):
    a = AccountFactory()
    t = SavingTypeFactory()

    form = SavingForm(
        user=main_user,
        today=TODAY,
        data={
            "date": "1999-01-01",
            "remark": "remark",
            "account": a.pk,
            "saving_type": t.pk,
        }
        | amounts,
    )

    assert form.is_valid()

    data = form.save()

    assert data.date == date(1999, 1, 1)
    assert data.price == expect_price
    assert data.fee == expect_fee
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


FUND_ERROR = "Fondas uždarytas 1999."
ACCOUNT_ERROR = (
    "Data negali būti vėlesnė nei sąskaitos uždarymo data. Sąskaita buvo uždaryta 1999."
)


@pytest.mark.parametrize(
    "fund_closed, account_closed, posted, errors",
    [
        pytest.param(
            1999, None, "2000-01-01", {"date": [FUND_ERROR]}, id="fund_after_closed"
        ),
        pytest.param(1999, None, "1999-12-31", {}, id="fund_closed_year"),
        pytest.param(1999, None, "1998-12-31", {}, id="fund_before_closed"),
        pytest.param(
            None,
            1999,
            "2000-03-01",
            {"date": [ACCOUNT_ERROR]},
            id="account_after_closed",
        ),
        pytest.param(None, 1999, "1999-12-31", {}, id="account_closed_year"),
        pytest.param(
            1999,
            1999,
            "2000-03-01",
            {"date": [FUND_ERROR, ACCOUNT_ERROR]},
            id="fund_and_account_after_closed",
        ),
    ],
)
def test_saving_date_after_the_parent_closed(
    main_user, fund_closed, account_closed, posted, errors
):
    main_user.journal.first_record = date(1998, 1, 1)
    main_user.journal.save()
    a = AccountFactory(closed=account_closed)
    t = SavingTypeFactory(closed=fund_closed)

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
