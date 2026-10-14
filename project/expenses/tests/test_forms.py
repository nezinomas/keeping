from datetime import date
from io import BytesIO

import pytest
import time_machine
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from ...accounts.tests.factories import AccountFactory
from ..forms import ExpenseForm, ExpenseNameForm, ExpenseTypeForm
from .factories import ExpenseFactory, ExpenseNameFactory, ExpenseTypeFactory

pytestmark = pytest.mark.django_db

one_pixel_gif = (
    b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04"
    b"\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02"
    b"\x02\x4c\x01\x00\x3b"
)


@pytest.fixture
def account():
    return AccountFactory()


@pytest.fixture
def expense_name():
    return ExpenseNameFactory(parent=ExpenseTypeFactory())


def _expense_data(account, expense_name, **overrides):
    """Valid ExpenseForm data; the type is the name's parent."""
    return {
        "date": "1999-01-01",
        "price": 112,
        "quantity": 1,
        "expense_type": expense_name.parent.pk,
        "expense_name": expense_name.pk,
        "account": account.pk,
        "remark": "",
        **overrides,
    }


def _saved_with_title(form_class, title, parent):
    """The type, or the name under `parent`, that `form_class` creates."""
    if form_class is ExpenseNameForm:
        return ExpenseNameFactory(title=title, parent=parent)
    return ExpenseTypeFactory(title=title)


@pytest.mark.parametrize(
    ("form_class", "field", "widget_type"),
    [
        (ExpenseForm, "date", "datepicker"),
        (ExpenseForm, "account", "select"),
        (ExpenseForm, "expense_type", "select"),
        (ExpenseForm, "expense_name", "select"),
        (ExpenseForm, "total_sum", "text"),
        (ExpenseForm, "quantity", "number"),
        (ExpenseForm, "price", "text"),
        (ExpenseForm, "remark", "textarea"),
        (ExpenseForm, "exception", "checkbox"),
        (ExpenseForm, "attachment", "clearablefile"),
        (ExpenseTypeForm, "title", "text"),
        (ExpenseTypeForm, "necessary", "checkbox"),
    ],
)
def test_form_field_widgets(main_user, form_class, field, widget_type):
    form = form_class(user=main_user)

    assert "user" not in form.fields
    assert form[field].widget_type == widget_type


def test_expense_form_widget_attributes(main_user):
    form = ExpenseForm(user=main_user)

    assert form["date"].field.widget.input_type == "text"
    assert form["total_sum"].field.widget.attrs["inputmode"] == "decimal"
    assert form["price"].field.widget.attrs["readonly"]
    assert "class" not in form["price"].field.widget.attrs


@time_machine.travel("1974-03-07")
def test_expense_initial_date_is_today_in_the_users_year(main_user):
    assert main_user.year == 1999

    form = ExpenseForm(user=main_user).as_p()

    assert '<input type="text" name="date" value="1999-03-07"' in form


@pytest.mark.parametrize(
    "form_class", [ExpenseForm, ExpenseNameForm], ids=lambda c: c.__name__
)
def test_form_offers_only_the_current_users_expense_types(
    main_user, second_user, form_class
):
    t1 = ExpenseTypeFactory(title="T1")
    ExpenseTypeFactory(title="T2", journal=second_user.journal)

    form = form_class(user=main_user).as_p()

    assert f'<option value="{t1.pk}">T1</option>' in form
    assert "T2" not in form


def test_expense_select_first_account(main_user, second_user):
    AccountFactory(title="A1", journal=second_user.journal)
    a2 = AccountFactory(title="A2")
    AccountFactory(title="A3")

    form = ExpenseForm(user=main_user).as_p()

    expect = f'<option value="{a2.pk}" selected>{a2}</option>'
    assert expect in form


def test_expense_edit_offers_the_account_open_in_the_expense_year(
    main_user, expense_name
):
    account = AccountFactory(closed=1998)
    expense = ExpenseFactory(
        date=date(1998, 6, 1),
        account=account,
        expense_type=expense_name.parent,
        expense_name=expense_name,
    )

    form = ExpenseForm(user=main_user, instance=expense)

    assert list(form.fields["account"].queryset) == [account]


def test_expense_edit_form_looks_up_no_default_account(
    main_user, django_assert_num_queries
):
    expense = ExpenseFactory()

    with django_assert_num_queries(0):
        ExpenseForm(user=main_user, instance=expense)


@pytest.mark.parametrize(
    ("posted", "cents"),
    [(0.01, 1), ("12,1", 1210)],
    ids=["point", "decimal_comma"],
)
def test_expense_form_valid_data(main_user, account, expense_name, posted, cents):
    form = ExpenseForm(
        user=main_user, data=_expense_data(account, expense_name, price=posted)
    )

    assert form.is_valid(), form.errors

    e = form.save()
    assert e.date == date(1999, 1, 1)
    assert e.price == cents
    assert e.expense_type == expense_name.parent
    assert e.expense_name == expense_name
    assert e.account == account
    assert e.quantity == 1


@pytest.mark.parametrize(
    ("posted", "errors"),
    [
        ("1999-06-01", {}),
        ("", {"date": ["Šis laukas yra privalomas."]}),
        (
            "2000-06-01",
            {
                "date": [
                    "Data negali būti vėlesnė nei sąskaitos uždarymo data. "
                    "Sąskaita buvo uždaryta 1999."
                ]
            },
        ),
    ],
)
def test_expense_date_is_valid_up_to_the_accounts_closed_year(
    main_user, expense_name, posted, errors
):
    form = ExpenseForm(
        user=main_user,
        data=_expense_data(AccountFactory(closed=1999), expense_name, date=posted),
    )

    assert form.errors == errors


def test_expense_form_quantity_starts_at_one(main_user):
    form = ExpenseForm(user=main_user)

    assert form["quantity"].value() == 1


@pytest.mark.parametrize("quantity, valid", [(0, False), (-1, False), (1, True)])
def test_expense_form_quantity_is_at_least_one(
    main_user, account, expense_name, quantity, valid
):
    form = ExpenseForm(
        user=main_user,
        data=_expense_data(account, expense_name, price=0.01, quantity=quantity),
    )

    assert form.is_valid() == valid
    assert ("quantity" in form.errors) == (not valid)


def test_expenses_form_blank_data(main_user):
    form = ExpenseForm(user=main_user, data={})

    assert not form.is_valid()

    errors = {
        "date": ["Šis laukas yra privalomas."],
        "price": ["Šis laukas yra privalomas."],
        "quantity": ["Šis laukas yra privalomas."],
        "expense_type": ["Šis laukas yra privalomas."],
        "expense_name": ["Šis laukas yra privalomas."],
        "account": ["Šis laukas yra privalomas."],
    }
    assert form.errors == errors


@pytest.mark.parametrize(
    "content, ext, valid",
    [
        pytest.param(one_pixel_gif, "gif", True, id="gif"),
        pytest.param(one_pixel_gif, "jpeg", True, id="jpeg"),
        pytest.param(one_pixel_gif, "png", True, id="png"),
        pytest.param(b"x", "pdf", False, id="pdf"),
        pytest.param(b"x", "txt", False, id="txt"),
        pytest.param(b"x", "doc", False, id="doc"),
        pytest.param(b"x", "xls", False, id="xls"),
    ],
)
def test_expenses_form_filefield(main_user, account, expense_name, content, ext, valid):
    attachment = SimpleUploadedFile(f"x.{ext}", content, content_type=f"image/{ext}")

    form = ExpenseForm(
        user=main_user,
        data=_expense_data(account, expense_name),
        files={"attachment": attachment},
    )

    assert form.is_valid() == valid


def test_expense_form_attachment_too_big(main_user, account, expense_name):
    pixels_per_side = 1200  # an RGB bmp this size is over the 4 MiB limit
    buffer = BytesIO()
    Image.new("RGB", (pixels_per_side, pixels_per_side)).save(buffer, "bmp")
    oversized = SimpleUploadedFile(
        "test.bmp", buffer.getvalue(), content_type="image/bmp"
    )

    form = ExpenseForm(
        user=main_user,
        data=_expense_data(account, expense_name),
        files={"attachment": oversized},
    )

    assert not form.is_valid()
    assert form.errors["attachment"] == ["Per didelis vaizdo failas ( > 4Mb)"]


@pytest.mark.parametrize(
    "overrides, expect",
    [
        pytest.param(
            {},
            {
                "exception": [
                    "Expense Type yra 'Būtina', todėl ji negali būti pažymėta kaip "
                    "'Išimtis'"
                ]
            },
            id="necessary_type",
        ),
        pytest.param(
            {"expense_type": ""},
            {
                "expense_type": ["Šis laukas yra privalomas."],
                "expense_name": [
                    "Pasirinkite tinkamą reikšmę. Parinkta reikšmė nėra galima."
                ],
            },
            id="no_type",
        ),
    ],
)
def test_expense_form_necessary_type_and_exception(
    main_user, account, overrides, expect
):
    necessary_type = ExpenseTypeFactory(necessary=True)
    expense_name = ExpenseNameFactory(parent=necessary_type)

    form = ExpenseForm(
        user=main_user,
        data=_expense_data(account, expense_name, exception=True, **overrides),
    )

    assert not form.is_valid()

    assert form.errors == expect


class _YearOverrideExpenseForm(ExpenseForm):
    def names_year(self):
        return 2005


@pytest.mark.parametrize(
    ("form_class", "kwargs", "query", "target"),
    [
        (ExpenseForm, {}, "", "id_expense_name"),
        (ExpenseForm, {"prefix": "form-3"}, "?prefix=form-3", "id_form-3-expense_name"),
        (_YearOverrideExpenseForm, {}, "?year=2005", "id_expense_name"),
    ],
    ids=["default", "prefix", "names_year"],
)
def test_expense_name_choices_mixin_hx_attributes(
    main_user, form_class, kwargs, query, target
):
    form = form_class(user=main_user, **kwargs).as_p()

    url = reverse("expenses:load_expense_name")
    assert f'hx-get="{url}{query}"' in form
    assert f'hx-target="#{target}"' in form
    assert 'hx-trigger="change"' in form


def test_expense_name_choices_mixin_keeps_translated_name_label(main_user):
    form = ExpenseForm(user=main_user).as_p()

    assert '<label for="id_expense_name">Išlaidų pavadinimas:</label>' in form


def test_expense_name_choices_mixin_names_year_filters_names(main_user):
    t = ExpenseTypeFactory()
    n_2005 = ExpenseNameFactory(title="N-2005", parent=t, valid_for=2005)
    ExpenseNameFactory(title="N-1999", parent=t, valid_for=1999)

    form = _YearOverrideExpenseForm(user=main_user, initial={"expense_type": t.pk})

    assert list(form.fields["expense_name"].queryset) == [n_2005]


@pytest.mark.parametrize(
    ("posted", "expect"),
    [(False, "N1"), (True, "N2")],
    ids=["initial", "posted_overrides_initial"],
)
def test_expense_name_choices_mixin_type_fills_names(main_user, posted, expect):
    t1 = ExpenseTypeFactory(title="T1")
    t2 = ExpenseTypeFactory(title="T2")
    names = {
        "N1": ExpenseNameFactory(title="N1", parent=t1),
        "N2": ExpenseNameFactory(title="N2", parent=t2),
    }
    kwargs = {}
    if posted:
        kwargs["data"] = {"expense_type": t2.pk}

    form = ExpenseForm(user=main_user, initial={"expense_type": t1.pk}, **kwargs)

    assert list(form.fields["expense_name"].queryset) == [names[expect]]


def test_expense_name_choices_mixin_instance_type_fills_names(main_user):
    t = ExpenseTypeFactory(title="T")
    n = ExpenseNameFactory(title="N", parent=t)
    ExpenseNameFactory(title="Other", parent=ExpenseTypeFactory(title="Other"))

    form = ExpenseForm(user=main_user, instance=ExpenseFactory(expense_type=t))

    assert list(form.fields["expense_name"].queryset) == [n]


def test_expense_type_valid_data(main_user):
    form = ExpenseTypeForm(user=main_user, data={"title": "Title", "necessary": True})

    assert form.is_valid()

    data = form.save()

    assert data.title == "Title"
    assert data.necessary
    assert data.journal.title == "bob Journal"
    assert data.journal == main_user.journal


@pytest.mark.parametrize(
    "form_class, required_fields",
    [
        pytest.param(ExpenseTypeForm, {"title"}, id="type"),
        pytest.param(ExpenseNameForm, {"title", "parent"}, id="name"),
    ],
)
def test_form_blank_data_requires(main_user, form_class, required_fields):
    form = form_class(user=main_user, data={})

    assert not form.is_valid()

    assert set(form.errors) == required_fields


# Posted to both forms: ExpenseTypeForm has no `parent` field and ignores it.
@pytest.mark.parametrize(
    "form_class, title",
    [
        pytest.param(ExpenseTypeForm, "aa", id="type-title_too_short"),
        pytest.param(ExpenseTypeForm, "a" * 255, id="type-title_too_long"),
        pytest.param(ExpenseNameForm, "x", id="name-title_too_short"),
        pytest.param(ExpenseNameForm, "a" * 255, id="name-title_too_long"),
    ],
)
def test_form_rejects_a_bad_title(main_user, form_class, title):
    parent = ExpenseTypeFactory()

    form = form_class(user=main_user, data={"title": title, "parent": parent.pk})

    assert not form.is_valid()

    assert "title" in form.errors


@pytest.mark.parametrize(
    "form_class",
    [
        pytest.param(ExpenseTypeForm, id="type"),
        pytest.param(ExpenseNameForm, id="name"),
    ],
)
def test_form_rejects_a_title_with_no_latin_letter_or_digit(main_user, form_class):
    parent = ExpenseTypeFactory()

    form = form_class(user=main_user, data={"title": "...", "parent": parent.pk})

    assert not form.is_valid()

    assert form.errors["title"] == [
        "Pavadinime turi būti bent viena lotyniška raidė arba skaitmuo."
    ]


@pytest.mark.parametrize(
    "title, errors",
    [
        pytest.param("savings", ["Šis pavadinimas rezervuotas."], id="savings"),
        pytest.param("total", ["Šis pavadinimas rezervuotas."], id="total"),
        pytest.param("date", ["Šis pavadinimas rezervuotas."], id="date"),
        pytest.param("Savings", [], id="case_differs"),
    ],
)
def test_expense_type_form_reserves_the_month_table_keys(main_user, title, errors):
    form = ExpenseTypeForm(user=main_user, data={"title": title})

    assert form.is_valid() == (not errors)

    assert form.errors.get("title", []) == errors


def test_expense_name_title_expanding_character(main_user):
    parent = ExpenseTypeFactory()
    form = ExpenseNameForm(
        user=main_user, data={"title": "Pienas ½ l", "parent": parent.pk}
    )

    assert not form.is_valid()

    assert form.errors["title"] == ["Pavadinime negali būti „½“."]


@pytest.mark.parametrize(
    "valid_for",
    [pytest.param("2000", id="text"), pytest.param(2000, id="number")],
)
def test_expense_name_valid_data(main_user, valid_for):
    p = ExpenseTypeFactory()

    form = ExpenseNameForm(
        user=main_user, data={"title": "Title", "parent": p.pk, "valid_for": valid_for}
    )

    assert form.is_valid()

    data = form.save()

    assert data.title == "Title"
    assert data.valid_for == 2000


@pytest.mark.parametrize(
    "form_class, title, message",
    [
        pytest.param(ExpenseTypeForm, "Būstas", "„Būstas“ jau yra.", id="type"),
        pytest.param(ExpenseNameForm, "Pienas", "„Pienas“ jau yra.", id="name"),
    ],
)
def test_form_identical_title_names_the_existing_one(
    main_user, form_class, title, message
):
    parent = ExpenseTypeFactory(title="Maistas")
    _saved_with_title(form_class, title, parent)

    form = form_class(user=main_user, data={"title": title, "parent": parent.pk})

    assert not form.is_valid()
    assert form.errors["title"] == [message]


@pytest.mark.parametrize(
    "form_class, existing_title, title, message",
    [
        pytest.param(
            ExpenseTypeForm,
            "Būstas",
            "Bustas",
            "Pavadinimas per daug panašus į jau esantį „Būstas“.",
            id="type",
        ),
        pytest.param(
            ExpenseNameForm,
            "Pienas",
            "PIENAS ",
            "Pavadinimas per daug panašus į jau esantį „Pienas“.",
            id="name",
        ),
    ],
)
def test_form_slug_taken_names_the_existing_one(
    main_user, form_class, existing_title, title, message
):
    parent = ExpenseTypeFactory(title="Maistas")
    _saved_with_title(form_class, existing_title, parent)

    form = form_class(user=main_user, data={"title": title, "parent": parent.pk})

    assert not form.is_valid()
    assert form.errors["title"] == [message]


def test_expense_type_same_slug_in_second_journal_is_valid(main_user, second_user):
    ExpenseTypeFactory(title="Būstas", journal=second_user.journal)

    form = ExpenseTypeForm(user=main_user, data={"title": "Bustas"})

    assert form.is_valid()


@pytest.mark.parametrize("title", ["Būstas", "BŪSTAS"])
def test_expense_type_edit_keeping_its_slug_is_valid(title, main_user):
    expense_type = ExpenseTypeFactory(title="Būstas")

    form = ExpenseTypeForm(user=main_user, instance=expense_type, data={"title": title})

    assert form.is_valid()


@pytest.mark.parametrize("edit", [False, True], ids=["create", "edit"])
def test_expense_type_ignores_a_posted_journal(main_user, second_user, edit):
    kwargs = {}
    if edit:
        kwargs["instance"] = ExpenseTypeFactory(title="Mine", journal=main_user.journal)

    form = ExpenseTypeForm(
        user=main_user,
        **kwargs,
        data={"journal": second_user.journal.pk, "title": "Mine", "necessary": True},
    )

    assert form.is_valid()

    saved = form.save()
    saved.refresh_from_db()

    assert saved.journal == main_user.journal


@pytest.mark.parametrize("field", ["account", "expense_type", "expense_name"])
def test_expense_rejects_an_account_type_or_name_of_another_journal(
    main_user, second_user, field
):
    mine_type = ExpenseTypeFactory(title="Mine", journal=main_user.journal)
    theirs_type = ExpenseTypeFactory(title="Theirs", journal=second_user.journal)
    data = {
        "date": "1999-01-01",
        "price": 0.01,
        "quantity": 1,
        "account": AccountFactory(title="Mine", journal=main_user.journal).pk,
        "expense_type": mine_type.pk,
        "expense_name": ExpenseNameFactory(title="Mine", parent=mine_type).pk,
    }
    theirs_name = ExpenseNameFactory(title="Theirs", parent=theirs_type)
    # a foreign name comes with its own type, or the parent filter rejects it first
    foreign = {
        "account": {
            "account": AccountFactory(title="Theirs", journal=second_user.journal).pk
        },
        "expense_type": {"expense_type": theirs_type.pk},
        "expense_name": {
            "expense_type": theirs_type.pk,
            "expense_name": theirs_name.pk,
        },
    }

    form = ExpenseForm(user=main_user, data=data | foreign[field])

    assert not form.is_valid()
    assert field in form.errors


def test_expense_name_rejects_a_type_of_another_journal(main_user, second_user):
    theirs = ExpenseTypeFactory(title="Theirs", journal=second_user.journal)

    form = ExpenseNameForm(
        user=main_user, data={"parent": theirs.pk, "title": "Name", "valid_for": ""}
    )

    assert not form.is_valid()
    assert "parent" in form.errors
