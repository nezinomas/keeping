import re
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import render_to_string
from django.urls import reverse

from ...accounts.tests.factories import AccountFactory
from ..forms_import import ReviewFormSet, ReviewReceiptForm
from ..models import Expense, ExpenseKeyword
from ..receipts import reader
from ..receipts.errors import UnreadableReceiptTextError
from ..receipts.reader import ReceiptReader
from ..receipts.receipt import Receipt, ReceiptLine
from ..receipts.text_parser import TextReceiptParser
from ..views.expenses_import import REVIEW_TEMPLATE, _review_context
from .factories import ExpenseKeywordFactory, ExpenseNameFactory, ExpenseTypeFactory
from .receipts.pdfs import (
    EMPTY_TEXT_LAYOUT,
    FIXTURES,
    empty_text_receipt_pdf,
    table_pdf,
)

pytestmark = pytest.mark.django_db

BARBORA = FIXTURES / "barbora.pdf"


def _upload(name, content, content_type="application/pdf"):
    return SimpleUploadedFile(name, content, content_type=content_type)


def _barbora_file():
    return _upload("barbora.pdf", BARBORA.read_bytes())


def _upload_data(account, pdf, date="1999-01-05"):
    return {"date": date, "account": account.pk, "pdf": pdf}


def _management_data(total):
    return {
        "form-TOTAL_FORMS": str(total),
        "form-INITIAL_FORMS": "0",
        "form-MIN_NUM_FORMS": "0",
        "form-MAX_NUM_FORMS": "1000",
    }


def _row_data(index, **overrides):
    data = {
        f"form-{index}-title": "Row title",
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


def _receipt_data(account, **overrides):
    data = {
        "date": "1999-01-05",
        "account": account.pk,
        "total": "500",
        "shop_money": "0",
        "shop_money_line": "0",
    }
    data.update(overrides)
    return data


def _save_data(rows, account, **receipt_overrides):
    data = _management_data(len(rows))
    for index, row in enumerate(rows):
        data |= _row_data(index, **row)
    data |= _receipt_data(account, **receipt_overrides)
    return data


# ----------------------------------------------------------------------------
#                                                                       Import
# ----------------------------------------------------------------------------
def test_import_get_anonymous_redirects_to_login(client):
    url = reverse("expenses:import")
    response = client.get(url)

    assert response.status_code == 302


def test_import_get_200_renders_upload_form(main_user, client_logged):
    url = reverse("expenses:import")
    response = client_logged.get(url)

    assert response.status_code == 200
    assert "paper.min.css" in response.content.decode()
    assert 'class="paper-skin"' in response.content.decode()
    assert 'name="pdf"' in response.content.decode()


def test_import_post_non_pdf_file_error(main_user, client_logged):
    a = AccountFactory()
    url = reverse("expenses:import")

    response = client_logged.post(
        url,
        data=_upload_data(a, _upload("lydrastis.txt", b"x", "text/plain")),
    )

    assert response.status_code == 200
    assert "Galima importuoti tik PDF failus." in response.content.decode()


def test_import_post_unrecognised_pdf_error(main_user, client_logged, tmp_path):
    a = AccountFactory()
    path = table_pdf(
        tmp_path / "unknown.pdf",
        text_above="UNKNOWN SHOP",
        header=("Item", "Qty", "Sum"),
        rows=[("Apple", "2 vnt.", "1,20")],
    )
    url = reverse("expenses:import")

    response = client_logged.post(
        url,
        data=_upload_data(a, _upload("unknown.pdf", path.read_bytes())),
    )

    assert response.status_code == 200
    text = response.content.decode()
    assert "Šis PDF nėra palaikomos parduotuvės čekis." in text
    assert "form-0-title" not in text


def test_import_post_unreadable_receipt_error(main_user, client_logged):
    a = AccountFactory()
    url = reverse("expenses:import")

    with patch.object(ReceiptReader, "read", side_effect=UnreadableReceiptTextError):
        response = client_logged.post(
            url,
            data=_upload_data(a, _barbora_file(), date="1999-01-05"),
        )

    assert response.status_code == 200
    assert "Čekio nepavyko nuskaityti." in response.content.decode()


def test_import_post_receipt_with_no_lines_error(
    main_user, client_logged, tmp_path, monkeypatch
):
    monkeypatch.setattr(reader, "PARSERS", (TextReceiptParser(EMPTY_TEXT_LAYOUT),))
    path = empty_text_receipt_pdf(tmp_path / "empty.pdf")
    url = reverse("expenses:import")

    response = client_logged.post(
        url,
        data=_upload_data(AccountFactory(), _upload("empty.pdf", path.read_bytes())),
    )

    assert response.status_code == 200
    assert "Čekio nepavyko nuskaityti." in response.content.decode()


def test_import_post_corrupt_pdf_error(main_user, client_logged):
    a = AccountFactory()
    url = reverse("expenses:import")

    response = client_logged.post(
        url, data=_upload_data(a, _upload("notes.pdf", b"hello, not a pdf"))
    )

    assert response.status_code == 200
    assert "Čekio nepavyko nuskaityti." in response.content.decode()


def test_import_post_fixture_29_rows(main_user, client_logged):
    a = AccountFactory()
    url = reverse("expenses:import")

    response = client_logged.post(
        url,
        data=_upload_data(a, _barbora_file(), date="2026-09-18"),
    )

    assert response.status_code == 200
    formset = response.context["formset"]
    assert len(formset.forms) == 29


def test_import_post_kg_line_amount_is_one(main_user, client_logged):
    a = AccountFactory()
    url = reverse("expenses:import")

    receipt = ReceiptReader.read(BARBORA)
    kg_index = next(
        i
        for i, line in enumerate(receipt.lines)
        if line.amount == 1 and line.price == 280
    )

    response = client_logged.post(
        url,
        data=_upload_data(a, _barbora_file(), date="2026-09-18"),
    )

    formset = response.context["formset"]
    assert formset.forms[kg_index].initial["amount"] == 1


def test_import_post_jogurt_keyword_prefills_row(main_user, client_logged):
    a = AccountFactory()
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory(title="Pieno produktai", parent=t)
    ExpenseKeywordFactory(journal=main_user.journal, keyword="jogurt", expense_name=n)

    receipt = ReceiptReader.read(BARBORA)
    jogurt_index = next(
        i for i, line in enumerate(receipt.lines) if "jogurt" in line.title.casefold()
    )

    url = reverse("expenses:import")
    response = client_logged.post(
        url,
        data=_upload_data(a, _barbora_file(), date="2026-09-18"),
    )

    formset = response.context["formset"]
    row = formset.forms[jogurt_index]
    assert row.initial["expense_type"] == t
    assert row.initial["expense_name"] == n
    assert row.initial["keyword"] == "jogurt"


def test_import_post_unmatched_row_blank_option_selected(main_user, client_logged):
    a = AccountFactory()
    url = reverse("expenses:import")

    response = client_logged.post(
        url,
        data=_upload_data(a, _barbora_file(), date="2026-09-18"),
    )

    text = response.content.decode()
    assert 'value="" selected' in text


def test_import_post_every_skip_box_named_form_n_skip(main_user, client_logged):
    a = AccountFactory()
    url = reverse("expenses:import")

    response = client_logged.post(
        url,
        data=_upload_data(a, _barbora_file(), date="2026-09-18"),
    )

    text = response.content.decode()
    assert 'name="form-0-skip"' in text
    assert 'name="form-28-skip"' in text


def _section(text, tag):
    match = re.search(rf"<{tag}>.*?</{tag}>", text, re.DOTALL)
    return match.group(0)


def _shop_money_receipt():
    return _receipt(
        lines=(
            ReceiptLine(title="A", amount=1, price=500, is_deposit=False),
            ReceiptLine(title="B", amount=1, price=100, is_deposit=False),
        ),
        total=500,
        shop_money=100,
    )


def _receipt(**kwargs):
    lines = kwargs.pop(
        "lines",
        (ReceiptLine(title="A", amount=1, price=500, is_deposit=False),),
    )
    return Receipt(lines=lines, **kwargs)


def test_import_post_shop_money_radios_only_when_positive(main_user, client_logged):
    a = AccountFactory()
    url = reverse("expenses:import")
    receipt = _receipt(
        lines=(
            ReceiptLine(title="A", amount=1, price=500, is_deposit=False),
            ReceiptLine(title="B", amount=1, price=100, is_deposit=False),
        ),
        total=500,
        shop_money=100,
    )

    with patch.object(ReceiptReader, "read", return_value=receipt):
        response = client_logged.post(
            url,
            data=_upload_data(a, _barbora_file(), date="1999-01-05"),
        )

    text = response.content.decode()
    assert 'name="shop_money_line"' in text
    assert 'name="form-0-shop_money_line"' not in text


def test_import_post_shop_money_radios_are_drawn_as_form_checks(
    main_user, client_logged
):
    a = AccountFactory()
    receipt = _receipt(
        lines=(ReceiptLine(title="A", amount=1, price=600, is_deposit=False),),
        total=500,
        shop_money=100,
    )

    with patch.object(ReceiptReader, "read", return_value=receipt):
        response = client_logged.post(
            reverse("expenses:import"),
            data=_upload_data(a, _barbora_file(), date="1999-01-05"),
        )

    radio = '<input type="radio" class="form-check-input" name="shop_money_line"'
    assert radio in response.content.decode()


def test_import_post_no_shop_money_radios(main_user, client_logged):
    a = AccountFactory()
    url = reverse("expenses:import")
    receipt = _receipt(total=500, shop_money=0)

    with patch.object(ReceiptReader, "read", return_value=receipt):
        response = client_logged.post(
            url,
            data=_upload_data(a, _barbora_file(), date="1999-01-05"),
        )

    text = response.content.decode()
    assert 'name="shop_money_line"' in text
    assert 'type="radio"' not in text


def test_import_post_disagreeing_totals_shows_warning(main_user, client_logged):
    a = AccountFactory()
    url = reverse("expenses:import")
    receipt = _receipt(
        lines=(ReceiptLine(title="A", amount=1, price=500, is_deposit=False),),
        total=999,
    )

    with patch.object(ReceiptReader, "read", return_value=receipt):
        response = client_logged.post(
            url,
            data=_upload_data(a, _barbora_file(), date="1999-01-05"),
        )

    text = response.content.decode()
    assert '<p :hidden="!disagree">' in text
    assert "Sumos nesutampa" in text


def test_import_post_agreeing_totals_no_warning(main_user, client_logged):
    a = AccountFactory()
    url = reverse("expenses:import")
    receipt = _receipt(
        lines=(ReceiptLine(title="A", amount=1, price=500, is_deposit=False),),
        total=500,
    )

    with patch.object(ReceiptReader, "read", return_value=receipt):
        response = client_logged.post(
            url,
            data=_upload_data(a, _barbora_file(), date="1999-01-05"),
        )

    text = response.content.decode()
    assert '<p :hidden="!disagree" hidden>' in text


def test_import_review_thead_classes_without_shop_money(main_user, client_logged):
    a = AccountFactory()
    url = reverse("expenses:import")

    response = client_logged.post(
        url,
        data=_upload_data(a, _barbora_file(), date="2026-09-18"),
    )

    thead = _section(response.content.decode(), "thead")
    assert thead.count('class="text-left"') == 4
    assert thead.count('class="text-center"') == 1
    assert "<th>Kiekis</th>" in thead
    assert "<th>Kaina</th>" in thead


def test_import_review_thead_classes_with_shop_money(main_user, client_logged):
    a = AccountFactory()
    url = reverse("expenses:import")

    with patch.object(ReceiptReader, "read", return_value=_shop_money_receipt()):
        response = client_logged.post(
            url,
            data=_upload_data(a, _barbora_file(), date="1999-01-05"),
        )

    thead = _section(response.content.decode(), "thead")
    assert thead.count('class="text-left"') == 4
    assert thead.count('class="text-center"') == 2


def test_import_review_tfoot_two_rows_without_shop_money(main_user, client_logged):
    a = AccountFactory()
    url = reverse("expenses:import")

    response = client_logged.post(
        url,
        data=_upload_data(a, _barbora_file(), date="2026-09-18"),
    )

    tfoot = _section(response.content.decode(), "tfoot")
    assert tfoot.count('class="main__total"') == 2
    assert "Eilučių suma" in tfoot
    assert "Čekio suma" in tfoot
    assert "&middot;" not in tfoot
    assert "·" not in tfoot


def test_import_review_tfoot_three_rows_with_shop_money(main_user, client_logged):
    a = AccountFactory()
    url = reverse("expenses:import")

    with patch.object(ReceiptReader, "read", return_value=_shop_money_receipt()):
        response = client_logged.post(
            url,
            data=_upload_data(a, _barbora_file(), date="1999-01-05"),
        )

    tfoot = _section(response.content.decode(), "tfoot")
    assert tfoot.count('class="main__total"') == 3
    assert "Eilučių suma" in tfoot
    assert "Čekio suma" in tfoot
    assert "Parduotuvės pinigai" in tfoot
    assert "&middot;" not in tfoot
    assert "·" not in tfoot


def test_import_upload_row_wrapper_class(main_user, client_logged):
    url = reverse("expenses:import")

    response = client_logged.get(url)

    assert 'class="import-upload"' in response.content.decode()


# ----------------------------------------------------------------------------
#                                                                   ImportSave
# ----------------------------------------------------------------------------
def test_import_save_valid_creates_expenses_and_redirects(main_user, client_logged):
    a = AccountFactory()
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory(title="Pieno produktai", parent=t)

    data = _save_data(
        [
            {
                "title": "Naturalus jogurtas VILVI",
                "price": "5,00",
                "expense_type": t.pk,
                "expense_name": n.pk,
                "keyword": "jogurt",
            }
        ],
        a,
        date="1999-03-05",
    )

    url = reverse("expenses:import_save")
    response = client_logged.post(url, data=data)

    assert response.status_code == 200
    assert response["HX-Redirect"] == reverse("expenses:index", kwargs={"month": 3})
    assert Expense.objects.count() == 1
    expense = Expense.objects.get()
    assert expense.price == 500
    assert expense.expense_name == n
    assert ExpenseKeyword.objects.filter(keyword="jogurt", expense_name=n).exists()


def test_import_save_edited_price_is_saved(main_user, client_logged):
    a = AccountFactory()
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory(title="Pieno produktai", parent=t)

    data = _save_data(
        [
            {
                "price": "9,99",
                "expense_type": t.pk,
                "expense_name": n.pk,
                "keyword": "jogurt",
                "title": "Naturalus jogurtas VILVI",
            }
        ],
        a,
    )

    url = reverse("expenses:import_save")
    client_logged.post(url, data=data)

    assert Expense.objects.get().price == 999


def test_import_save_invalid_nothing_saved_names_intact(main_user, client_logged):
    a = AccountFactory()
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory(title="Pieno produktai", parent=t)

    data = _save_data(
        [
            {
                "title": "",  # missing required field on a non-skipped row
                "price": "5,00",
                "expense_type": t.pk,
                "expense_name": n.pk,
                "keyword": "jogurt",
            }
        ],
        a,
    )

    url = reverse("expenses:import_save")
    response = client_logged.post(url, data=data)

    assert response.status_code == 200
    assert Expense.objects.count() == 0
    formset = response.context["formset"]
    assert formset.forms[0].fields["expense_name"].queryset.filter(pk=n.pk).exists()


def test_import_save_tampered_account_refused(main_user, second_user, client_logged):
    a = AccountFactory(journal=second_user.journal)
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory(title="Pieno produktai", parent=t)

    data = _save_data(
        [
            {
                "title": "Naturalus jogurtas VILVI",
                "price": "5,00",
                "expense_type": t.pk,
                "expense_name": n.pk,
                "keyword": "jogurt",
            }
        ],
        a,
    )

    url = reverse("expenses:import_save")
    response = client_logged.post(url, data=data)

    assert response.status_code == 200
    assert Expense.objects.count() == 0
    assert "Pasirinkite tinkamą reikšmę" in response.content.decode()


def test_import_save_tampered_account_still_shows_shop_money_radios(
    main_user, second_user, client_logged
):
    a = AccountFactory(journal=second_user.journal)
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory(title="Pieno produktai", parent=t)

    data = _save_data(
        [
            {
                "title": "Naturalus jogurtas VILVI",
                "price": "5,00",
                "expense_type": t.pk,
                "expense_name": n.pk,
                "keyword": "jogurt",
            }
        ],
        a,
        shop_money="100",
        shop_money_line="0",
    )

    url = reverse("expenses:import_save")
    response = client_logged.post(url, data=data)

    assert response.status_code == 200
    assert Expense.objects.count() == 0
    text = response.content.decode()
    radio = '<input type="radio" class="form-check-input" name="shop_money_line"'
    assert radio in text
    assert re.search(r'name="shop_money_line" value="0"[^>]*\bchecked>', text)


def test_import_save_tampered_shop_money_line_out_of_range_refused(
    main_user, client_logged
):
    a = AccountFactory()
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory(title="Pieno produktai", parent=t)

    data = _save_data(
        [
            {
                "title": "Naturalus jogurtas VILVI",
                "price": "5,00",
                "expense_type": t.pk,
                "expense_name": n.pk,
                "keyword": "jogurt",
            }
        ],
        a,
        shop_money="100",
        shop_money_line="5",
    )

    url = reverse("expenses:import_save")
    response = client_logged.post(url, data=data)

    assert response.status_code == 200
    assert Expense.objects.count() == 0
    assert "Parduotuvės pinigų eilutės šiame čekyje nėra." in response.content.decode()


def test_import_save_tampered_expense_type_refused(
    main_user, second_user, client_logged
):
    a = AccountFactory()
    t = ExpenseTypeFactory(title="Foreign type", journal=second_user.journal)
    n = ExpenseNameFactory(title="Foreign name", parent=t)

    data = _save_data(
        [
            {
                "title": "Naturalus jogurtas VILVI",
                "price": "5,00",
                "expense_type": t.pk,
                "expense_name": n.pk,
                "keyword": "jogurt",
            }
        ],
        a,
    )

    url = reverse("expenses:import_save")
    response = client_logged.post(url, data=data)

    assert response.status_code == 200
    assert Expense.objects.count() == 0


# ----------------------------------------------------------------------------
#                                                                        Index
# ----------------------------------------------------------------------------
def test_index_shows_import_link(main_user, client_logged):
    url = reverse("expenses:index")
    response = client_logged.get(url)

    text = response.content.decode()
    assert "Importuoti čekį" in text
    assert reverse("expenses:import") in text
    assert 'class="button-outline-success import-receipt"' in text


def test_import_upload_file_control_speaks_the_app_language(main_user, client_logged):
    url = reverse("expenses:import")

    text = client_logged.get(url).content.decode()

    assert "Pasirinkti failą" in text
    assert 'data-empty="Failas nepasirinktas"' in text
    assert re.search(r'<input type="file" name="pdf"[^>]*class="visually-hidden"', text)


# ----------------------------------------------------------------------------
#                                                          Error markup, colspan
# ----------------------------------------------------------------------------
def test_import_save_invalid_title_shows_invalid_feedback(main_user, client_logged):
    a = AccountFactory()
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory(title="Pieno produktai", parent=t)

    data = _save_data(
        [
            {
                "title": "",
                "price": "5,00",
                "expense_type": t.pk,
                "expense_name": n.pk,
                "keyword": "jogurt",
            }
        ],
        a,
    )

    url = reverse("expenses:import_save")
    response = client_logged.post(url, data=data)

    text = response.content.decode()
    row = _section(text, "tbody")
    assert '<div class="invalid-feedback">' in row


def test_import_save_tampered_account_shows_invalid_feedback(
    main_user, second_user, client_logged
):
    a = AccountFactory(journal=second_user.journal)
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory(title="Pieno produktai", parent=t)

    data = _save_data(
        [
            {
                "title": "Naturalus jogurtas VILVI",
                "price": "5,00",
                "expense_type": t.pk,
                "expense_name": n.pk,
                "keyword": "jogurt",
            }
        ],
        a,
    )

    url = reverse("expenses:import_save")
    response = client_logged.post(url, data=data)

    text = response.content.decode()
    assert '<div class="invalid-feedback">Pasirinkite tinkamą reikšmę' in text


def test_import_save_shop_money_out_of_range_shows_invalid_feedback(
    main_user, client_logged
):
    a = AccountFactory()
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory(title="Pieno produktai", parent=t)

    data = _save_data(
        [
            {
                "title": "Naturalus jogurtas VILVI",
                "price": "5,00",
                "expense_type": t.pk,
                "expense_name": n.pk,
                "keyword": "jogurt",
            }
        ],
        a,
        shop_money="100",
        shop_money_line="5",
    )

    url = reverse("expenses:import_save")
    response = client_logged.post(url, data=data)

    text = response.content.decode()
    assert (
        '<div class="invalid-feedback">Parduotuvės pinigų eilutės šiame čekyje nėra.'
        in text
    )


def _tfoot_rows(text):
    tfoot = _section(text, "tfoot")
    return re.findall(r"<tr class=\"main__total\">.*?</tr>", tfoot, re.DOTALL)


def test_import_review_tfoot_cells_collapsed_without_shop_money(
    main_user, client_logged
):
    a = AccountFactory()
    url = reverse("expenses:import")

    response = client_logged.post(
        url,
        data=_upload_data(a, _barbora_file(), date="2026-09-18"),
    )

    text = response.content.decode()
    rows = _tfoot_rows(text)

    assert len(rows) == 2
    for row in rows:
        cells = re.findall(r"<td[^>]*>", row)
        assert len(cells) == 3
        assert 'colspan="3"' in cells[-1]
    assert "<td></td>" not in _section(text, "tfoot")


def test_import_review_tfoot_cells_collapsed_with_shop_money(main_user, client_logged):
    a = AccountFactory()
    url = reverse("expenses:import")

    with patch.object(ReceiptReader, "read", return_value=_shop_money_receipt()):
        response = client_logged.post(
            url,
            data=_upload_data(a, _barbora_file(), date="1999-01-05"),
        )

    text = response.content.decode()
    rows = _tfoot_rows(text)

    assert len(rows) == 3
    for row in rows:
        cells = re.findall(r"<td[^>]*>", row)
        assert len(cells) == 3
        assert 'colspan="4"' in cells[-1]
    assert "<td></td>" not in _section(text, "tfoot")


def test_import_review_row_error_colspan_with_shop_money(main_user, client_logged):
    a = AccountFactory()

    data = _save_data(
        [{"skip": "on"}],
        a,
        shop_money="100",
        shop_money_line="0",
    )

    url = reverse("expenses:import_save")
    response = client_logged.post(url, data=data)

    text = response.content.decode()
    assert "Parduotuvės pinigų negalima priskirti praleistai eilutei." in text
    match = re.search(
        r'<td colspan="(\d+)">\s*<div class="invalid-feedback">'
        r"Parduotuvės pinigų negalima priskirti praleistai eilutei\.",
        text,
    )
    assert match is not None
    assert match.group(1) == "8"


def test_import_review_row_error_colspan_without_shop_money(main_user):
    a = AccountFactory()
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory(title="Pieno produktai", parent=t)

    data = _save_data(
        [
            {
                "title": "Naturalus jogurtas VILVI",
                "price": "5,00",
                "expense_type": t.pk,
                "expense_name": n.pk,
                "keyword": "jogurt",
            }
        ],
        a,
    )

    receipt_form = ReviewReceiptForm(user=main_user, data=data)
    assert receipt_form.is_valid()

    formset = ReviewFormSet(
        data=data,
        shop_money=0,
        shop_money_line=0,
        form_kwargs={
            "user": main_user,
            "year": receipt_form.cleaned_data["date"].year,
        },
    )
    assert formset.is_valid()
    formset.forms[0].add_error(None, "Test forced row error.")

    context = _review_context(
        receipt_form,
        formset,
        lines_total=500,
        receipt_total=500,
        shop_money=0,
        shop_money_line=0,
    )

    html = render_to_string(REVIEW_TEMPLATE, context)

    match = re.search(
        r'<td colspan="(\d+)">\s*<div class="invalid-feedback">'
        r"Test forced row error\.",
        html,
    )
    assert match is not None
    assert match.group(1) == "7"
