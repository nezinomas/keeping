from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from ....accounts.tests.factories import AccountFactory
from ....pensions.tests.factories import PensionTypeFactory
from ...forms import AccountWorthForm, PensionWorthForm, SavingWorthForm
from ...services.model_services import SavingWorthModelService
from ..factories import SavingTypeFactory
from ..helper import worth_form

pytestmark = pytest.mark.django_db

TODAY = date(1999, 2, 2)
NOW = datetime(1999, 2, 2, 3, 2, 1, tzinfo=timezone.utc)


WORTH_FORMS = pytest.mark.parametrize(
    "form_class, factory, field",
    [
        pytest.param(SavingWorthForm, SavingTypeFactory, "saving_type", id="saving"),
        pytest.param(AccountWorthForm, AccountFactory, "account", id="account"),
        pytest.param(
            PensionWorthForm, PensionTypeFactory, "pension_type", id="pension"
        ),
    ],
)


@WORTH_FORMS
def test_worth_form_fields(main_user, form_class, factory, field):
    form = worth_form(form_class, main_user, today=TODAY, now=NOW).as_p()

    assert '<input type="text" name="price"' in form
    assert f'<select name="{field}"' in form


@WORTH_FORMS
@pytest.mark.parametrize(
    "price, cents",
    [
        pytest.param("0.01", 1, id="a_cent"),
        pytest.param("12,1", 1210, id="decimal_comma"),
        pytest.param("0", 0, id="reset"),
    ],
)
def test_worth_form_valid_data(main_user, form_class, factory, field, price, cents):
    related = factory()

    form = worth_form(
        form_class,
        main_user,
        today=TODAY,
        now=NOW,
        data={"date": "1999-1-2", "price": price, field: related.pk},
    )
    assert form.is_valid(), form.errors

    data = form.save()

    assert data.date == datetime(1999, 1, 2, 3, 2, 1, tzinfo=timezone.utc)
    assert data.price == cents
    assert data.serializable_value(field) == related.pk


@WORTH_FORMS
def test_worth_form_date_starts_at_today_in_the_users_year(
    main_user, form_class, factory, field
):
    form = worth_form(form_class, main_user, today=date(2005, 3, 4), now=NOW)

    assert form["date"].value() == datetime(main_user.year, 3, 4)


@WORTH_FORMS
def test_worth_form_blank_data(main_user, form_class, factory, field):
    form = worth_form(form_class, main_user, today=TODAY, now=NOW, data={})

    assert not form.is_valid()

    assert field in form.errors


@pytest.mark.parametrize(
    "form_class, factory, field, message",
    [
        pytest.param(
            SavingWorthForm,
            SavingTypeFactory,
            "saving_type",
            "Fondas uždarytas 1999.",
            id="saving",
        ),
        pytest.param(
            AccountWorthForm,
            AccountFactory,
            "account",
            "Sąskaita uždaryta 1999.",
            id="account",
        ),
    ],
)
@pytest.mark.parametrize(
    "date, closed_error",
    [
        pytest.param("2000-1-1", True, id="after_closed"),
        pytest.param("1999-12-31", False, id="closed_year"),
        pytest.param("1998-12-31", False, id="before_closed"),
    ],
)
def test_worth_form_date_after_the_fund_closed(
    main_user, form_class, factory, field, message, date, closed_error
):
    fund = factory(closed=1999)

    form = worth_form(
        form_class,
        main_user,
        today=TODAY,
        now=NOW,
        data={"date": date, "price": "1.0", field: fund.pk},
    )

    assert form.is_valid() is not closed_error
    assert form.errors.get("date", []) == ([message] if closed_error else [])


@pytest.mark.parametrize("picked", ["2000-01-01", "1999-12-31"])
@pytest.mark.parametrize(
    "clock",
    [
        datetime(2000, 1, 1, 0, 30, tzinfo=ZoneInfo("Europe/Vilnius")),
        datetime(1999, 12, 31, 23, 30, tzinfo=ZoneInfo("Europe/Vilnius")),
    ],
)
def test_a_worth_counts_in_the_year_it_was_picked_for(picked, clock, main_user):
    form = worth_form(
        SavingWorthForm,
        main_user,
        today=TODAY,
        now=clock.astimezone(timezone.utc),
        data={"date": picked, "price": "1", "saving_type": SavingTypeFactory().pk},
    )
    assert form.is_valid()
    form.save()

    actual = SavingWorthModelService(main_user).have()

    assert [x["year"] for x in actual] == [int(picked[:4])]
