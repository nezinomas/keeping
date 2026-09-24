from datetime import date

import pytest
import time_machine
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from ...accounts.tests.factories import AccountFactory
from ..forms_import import (
    ReceiptUploadForm,
    ReviewFormSet,
    ReviewLineForm,
    ReviewReceiptForm,
)
from ..receipts.receipt import Receipt, ReceiptLine
from ..services.model_services import ExpenseKeywordModelService
from .factories import ExpenseKeywordFactory, ExpenseNameFactory, ExpenseTypeFactory

pytestmark = pytest.mark.django_db


def _pdf(name="lydrastis.pdf"):
    return SimpleUploadedFile(name, b"%PDF-1.4", content_type="application/pdf")


# ----------------------------------------------------------------------------
#                                                          ReceiptUploadForm
# ----------------------------------------------------------------------------
def test_upload_form_non_pdf_refused(main_user):
    a = AccountFactory()
    f = SimpleUploadedFile("lydrastis.txt", b"x", content_type="text/plain")

    form = ReceiptUploadForm(
        user=main_user,
        data={"date": "1999-01-01", "account": a.pk},
        files={"pdf": f},
    )

    assert not form.is_valid()
    assert form.errors["pdf"] == ["Galima importuoti tik PDF failus."]


def test_upload_form_uppercase_pdf_accepted(main_user):
    a = AccountFactory()
    f = SimpleUploadedFile("lydrastis.PDF", b"%PDF-1.4", content_type="application/pdf")

    form = ReceiptUploadForm(
        user=main_user,
        data={"date": "1999-01-01", "account": a.pk},
        files={"pdf": f},
    )

    assert form.is_valid(), form.errors


@time_machine.travel("1974-01-01")
def test_upload_form_date_initial(main_user):
    form = ReceiptUploadForm(user=main_user).as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form


def test_upload_form_account_initial_first(main_user, second_user):
    AccountFactory(title="A1", journal=second_user.journal)
    a2 = AccountFactory(title="A2")

    form = ReceiptUploadForm(user=main_user).as_p()

    assert f'<option value="{a2.pk}" selected>{a2}</option>' in form


def test_upload_form_another_journal_account_refused(main_user, second_user):
    a = AccountFactory(journal=second_user.journal)

    form = ReceiptUploadForm(
        user=main_user,
        data={"date": "1999-01-01", "account": a.pk},
        files={"pdf": _pdf()},
    )

    assert not form.is_valid()
    assert "account" in form.errors


# ----------------------------------------------------------------------------
#                                                          ReviewReceiptForm
# ----------------------------------------------------------------------------
def test_review_receipt_form_another_journal_account_refused(main_user, second_user):
    a = AccountFactory(journal=second_user.journal)

    form = ReviewReceiptForm(
        user=main_user,
        data={
            "date": "1999-01-01",
            "account": a.pk,
            "total": 100,
            "shop_money": 0,
            "shop_money_line": 0,
        },
    )

    assert not form.is_valid()
    assert "account" in form.errors


def test_review_receipt_form_initial_from_most_expensive_line():
    a = AccountFactory()
    receipt = Receipt(
        lines=(
            ReceiptLine(title="A", amount=1, price=100, is_deposit=False),
            ReceiptLine(title="B", amount=1, price=300, is_deposit=False),
            ReceiptLine(title="C", amount=1, price=300, is_deposit=False),
        ),
        total=594,
        shop_money=6,
    )

    initial = ReviewReceiptForm.initial_from(receipt, date(1999, 1, 1), a)

    assert initial == {
        "date": date(1999, 1, 1),
        "account": a,
        "total": 594,
        "shop_money": 6,
        "shop_money_line": 1,
    }


def test_review_receipt_form_initial_from_no_shop_money():
    a = AccountFactory()
    receipt = Receipt(
        lines=(ReceiptLine(title="A", amount=1, price=500, is_deposit=False),),
        total=500,
    )

    initial = ReviewReceiptForm.initial_from(receipt, date(1999, 1, 1), a)

    assert initial["shop_money_line"] == 0


# ----------------------------------------------------------------------------
#                                                             ReviewLineForm
# ----------------------------------------------------------------------------
def _line_data(**overrides):
    data = {
        "title": "Naturalus jogurtas VILVI",
        "amount": "1",
        "price": "1,00",
        "expense_type": "",
        "expense_name": "",
        "keyword": "",
        "skip": "",
        "is_deposit": "",
    }
    data.update(overrides)
    return data


def test_line_form_hx_get_carries_prefix_and_year(main_user):
    form = ReviewLineForm(user=main_user, year=2005, prefix="form-3")
    rendered = form.as_p()

    url = reverse("expenses:load_expense_name")
    assert f'hx-get="{url}?prefix=form-3&amp;year=2005"' in rendered


def test_line_form_names_offered_for_import_year(main_user):
    t = ExpenseTypeFactory()
    n_2005 = ExpenseNameFactory(title="N-2005", parent=t, valid_for=2005)
    ExpenseNameFactory(title="N-1999", parent=t, valid_for=1999)

    form = ReviewLineForm(user=main_user, year=2005, initial={"expense_type": t.pk})

    assert list(form.fields["expense_name"].queryset) == [n_2005]


@pytest.mark.parametrize(
    "missing", ["title", "amount", "price", "expense_type", "expense_name", "keyword"]
)
def test_line_form_required_field_on_non_skipped_row(main_user, missing):
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory(parent=t, title="Pieno produktai")

    data = _line_data(
        expense_type=t.pk,
        expense_name=n.pk,
        keyword="jogurt",
    )
    data[missing] = ""

    form = ReviewLineForm(user=main_user, year=1999, data=data)

    assert not form.is_valid()
    assert form.errors[missing] == ["Šis laukas yra privalomas."]


def test_line_form_skipped_row_blank_is_valid(main_user):
    data = _line_data(
        title="",
        amount="",
        price="abc",
        expense_type="",
        expense_name="",
        keyword="",
        skip="on",
    )

    form = ReviewLineForm(user=main_user, year=1999, data=data)

    assert form.is_valid(), form.errors


def test_line_form_price_must_be_greater_than_zero(main_user):
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory(parent=t, title="Pieno produktai")

    data = _line_data(
        price="0",
        expense_type=t.pk,
        expense_name=n.pk,
        keyword="jogurt",
    )

    form = ReviewLineForm(user=main_user, year=1999, data=data)

    assert not form.is_valid()
    assert form.errors["price"] == ["Kaina turi būti didesnė už nulį."]


def test_line_form_amount_must_be_greater_than_zero(main_user):
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory(parent=t, title="Pieno produktai")

    data = _line_data(
        amount="0",
        expense_type=t.pk,
        expense_name=n.pk,
        keyword="jogurt",
    )

    form = ReviewLineForm(user=main_user, year=1999, data=data)

    assert not form.is_valid()
    assert form.errors["amount"] == ["Kiekis turi būti didesnis už nulį."]


def test_line_form_keyword_too_short(main_user):
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory(parent=t, title="Pieno produktai")

    data = _line_data(expense_type=t.pk, expense_name=n.pk, keyword="jo")

    form = ReviewLineForm(user=main_user, year=1999, data=data)

    assert not form.is_valid()
    assert form.errors["keyword"] == ["Raktažodis turi būti bent 3 simbolių."]


def test_line_form_keyword_not_in_title(main_user):
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory(parent=t, title="Pieno produktai")

    data = _line_data(
        title="Bananai",
        expense_type=t.pk,
        expense_name=n.pk,
        keyword="obuoliai",
    )

    form = ReviewLineForm(user=main_user, year=1999, data=data)

    assert not form.is_valid()
    assert form.errors["keyword"] == ["Raktažodis turi būti prekės pavadinime."]


def test_line_form_keyword_found_only_in_edited_title_passes(main_user):
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory(parent=t, title="Vaisiai")

    data = _line_data(
        title="Kivis, pataisytas pavadinimas",
        expense_type=t.pk,
        expense_name=n.pk,
        keyword="kivis",
    )

    form = ReviewLineForm(user=main_user, year=1999, data=data)

    assert form.is_valid(), form.errors


def test_line_form_keyword_stored_normalised(main_user):
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory(parent=t, title="Pieno produktai")

    data = _line_data(
        title="Naturalus Jogurtas VILVI",
        expense_type=t.pk,
        expense_name=n.pk,
        keyword="  Jogurt ",
    )

    form = ReviewLineForm(user=main_user, year=1999, data=data)

    assert form.is_valid(), form.errors
    assert form.cleaned_data["keyword"] == "jogurt"


def test_line_form_another_journal_type_refused(main_user, second_user):
    t = ExpenseTypeFactory(title="Foreign type", journal=second_user.journal)
    n = ExpenseNameFactory(title="Foreign name", parent=t)

    data = _line_data(expense_type=t.pk, expense_name=n.pk, keyword="jogurt")

    form = ReviewLineForm(user=main_user, year=1999, data=data)

    assert not form.is_valid()
    assert "expense_type" in form.errors


def test_line_form_name_of_another_type_refused(main_user):
    t1 = ExpenseTypeFactory(title="T1")
    t2 = ExpenseTypeFactory(title="T2")
    n2 = ExpenseNameFactory(title="N2", parent=t2)

    data = _line_data(expense_type=t1.pk, expense_name=n2.pk, keyword="jogurt")

    form = ReviewLineForm(user=main_user, year=1999, data=data)

    assert not form.is_valid()
    assert "expense_name" in form.errors


# ----------------------------------------------------------------------------
#                                                              ReviewFormSet
# ----------------------------------------------------------------------------
def _management_data(total):
    return {
        "form-TOTAL_FORMS": str(total),
        "form-INITIAL_FORMS": "0",
        "form-MIN_NUM_FORMS": "0",
        "form-MAX_NUM_FORMS": "1000",
    }


def _row_data(index, **overrides):
    data = {
        f"form-{index}-title": "Naturalus jogurtas VILVI",
        f"form-{index}-amount": "1",
        f"form-{index}-price": "5,00",
        f"form-{index}-expense_type": "",
        f"form-{index}-expense_name": "",
        f"form-{index}-keyword": "",
        f"form-{index}-skip": "",
        f"form-{index}-is_deposit": "",
    }
    for key, value in overrides.items():
        data[f"form-{index}-{key}"] = value
    return data


def _formset(data, main_user, shop_money=0, shop_money_line=0):
    return ReviewFormSet(
        data=data,
        shop_money=shop_money,
        shop_money_line=shop_money_line,
        form_kwargs={"user": main_user, "year": 1999},
    )


def test_formset_duplicate_keyword_different_names_errors_both(main_user):
    t = ExpenseTypeFactory()
    n1 = ExpenseNameFactory(title="N1", parent=t)
    n2 = ExpenseNameFactory(title="N2", parent=t)

    data = _management_data(2)
    data |= _row_data(0, expense_type=t.pk, expense_name=n1.pk, keyword="jogurt")
    data |= _row_data(1, expense_type=t.pk, expense_name=n2.pk, keyword="jogurt")

    formset = _formset(data, main_user)

    assert not formset.is_valid()
    msg = "Tas pats raktažodis naudojamas skirtingiems išlaidų pavadinimams."
    assert formset.forms[0].errors["keyword"] == [msg]
    assert formset.forms[1].errors["keyword"] == [msg]


def test_formset_same_keyword_same_name_valid(main_user):
    t = ExpenseTypeFactory()
    n1 = ExpenseNameFactory(title="N1", parent=t)

    data = _management_data(2)
    data |= _row_data(0, expense_type=t.pk, expense_name=n1.pk, keyword="jogurt")
    data |= _row_data(1, expense_type=t.pk, expense_name=n1.pk, keyword="jogurt")

    formset = _formset(data, main_user)

    assert formset.is_valid(), formset.errors


def test_formset_shop_money_on_skipped_row(main_user):
    data = _management_data(1)
    data |= _row_data(0, skip="on")

    formset = _formset(data, main_user, shop_money=100, shop_money_line=0)

    assert not formset.is_valid()
    msg = "Parduotuvės pinigų negalima priskirti praleistai eilutei."
    assert formset.forms[0].non_field_errors() == [msg]


def test_formset_shop_money_line_out_of_range(main_user):
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory(parent=t, title="Pieno produktai")

    data = _management_data(1)
    data |= _row_data(0, expense_type=t.pk, expense_name=n.pk, keyword="jogurt")

    formset = _formset(data, main_user, shop_money=100, shop_money_line=5)

    assert not formset.is_valid()
    msg = "Parduotuvės pinigų negalima priskirti praleistai eilutei."
    assert formset.non_form_errors() == [msg]


def test_formset_shop_money_leaves_price_zero_or_below(main_user):
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory(parent=t, title="Pieno produktai")

    data = _management_data(1)
    data |= _row_data(
        0,
        price="1,00",
        expense_type=t.pk,
        expense_name=n.pk,
        keyword="jogurt",
    )

    formset = _formset(data, main_user, shop_money=100, shop_money_line=0)

    assert not formset.is_valid()
    msg = "Parduotuvės pinigai šią kainą padarytų nulinę arba neigiamą."
    assert formset.forms[0].errors["price"] == [msg]


def test_formset_disagreeing_totals_still_valid(main_user):
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory(parent=t, title="Pieno produktai")

    data = _management_data(1)
    data |= _row_data(
        0,
        price="999,00",
        expense_type=t.pk,
        expense_name=n.pk,
        keyword="jogurt",
    )

    formset = _formset(data, main_user)

    assert formset.is_valid(), formset.errors


def test_formset_reviewed_lines(main_user):
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory(parent=t, title="Pieno produktai")

    data = _management_data(2)
    data |= _row_data(
        0,
        price="5,00",
        expense_type=t.pk,
        expense_name=n.pk,
        keyword="jogurt",
    )
    data |= _row_data(1, skip="on")

    formset = _formset(data, main_user, shop_money=100, shop_money_line=0)

    assert formset.is_valid(), formset.errors

    lines = formset.reviewed_lines()

    assert len(lines) == 1
    assert lines[0].line.price == 500
    assert lines[0].line.title == "Naturalus jogurtas VILVI"
    assert lines[0].expense_name == n
    assert lines[0].keyword == "jogurt"
    assert lines[0].carries_shop_money is True


def test_formset_initial_from_prefills_matched_row_and_leaves_unmatched_blank(
    main_user,
):
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory(title="Pieno produktai", parent=t)
    ExpenseKeywordFactory(journal=main_user.journal, keyword="jogurt", expense_name=n)

    receipt = Receipt(
        lines=(
            ReceiptLine(
                title="Naturalus jogurtas VILVI", amount=1, price=100, is_deposit=False
            ),
            ReceiptLine(title="Nezinoma preke", amount=1, price=200, is_deposit=False),
        ),
        total=300,
    )
    keywords = ExpenseKeywordModelService(main_user).year(1999)

    initial = ReviewFormSet.initial_from(receipt, keywords)

    assert initial[0]["title"] == "Naturalus jogurtas VILVI"
    assert initial[0]["price"] == 1.0
    assert initial[0]["expense_name"] == n
    assert initial[0]["keyword"] == "jogurt"
    assert "expense_name" not in initial[1]
    assert "keyword" not in initial[1]


def test_formset_initial_from_weighed_line_amount_is_one(main_user):
    receipt = Receipt(
        lines=(ReceiptLine(title="Svoris", amount=1, price=250, is_deposit=False),),
        total=250,
    )

    initial = ReviewFormSet.initial_from(receipt, [])

    assert initial[0]["amount"] == 1
