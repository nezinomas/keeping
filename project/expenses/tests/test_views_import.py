import re
from datetime import date
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import render_to_string
from django.urls import reverse

from ...accounts.tests.factories import AccountFactory
from ...core.tests.utils import count_queries
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
UPLOAD_DATE = date(1999, 1, 5)
REVIEW_DATE = date(2026, 9, 18)


def _upload(name, content, content_type="application/pdf"):
    return SimpleUploadedFile(name, content, content_type=content_type)


def _barbora_file():
    return _upload("barbora.pdf", BARBORA.read_bytes())


def _upload_data(account, pdf, on):
    return {"date": on.isoformat(), "account": account.pk, "pdf": pdf}


def _post_upload(client, account, pdf, on=UPLOAD_DATE):
    return client.post(reverse("expenses:import"), data=_upload_data(account, pdf, on))


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


def _receipt_data(account, on, **overrides):
    data = {
        "date": on.isoformat(),
        "account": account.pk,
        "total": "500",
        "shop_money": "0",
        "shop_money_line": "0",
    }
    data.update(overrides)
    return data


def _save_data(rows, account, on=UPLOAD_DATE, **receipt_overrides):
    data = _management_data(len(rows))
    for index, row in enumerate(rows):
        data |= _row_data(index, **row)
    data |= _receipt_data(account, on, **receipt_overrides)
    return data


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


def _n_line_receipt(n):
    lines = tuple(
        ReceiptLine(title=f"Product {i}", amount=1, price=100 + i, is_deposit=False)
        for i in range(n)
    )
    return Receipt(lines=lines, total=sum(line.price for line in lines))


def _post_review(client, account, receipt, on=UPLOAD_DATE):
    with patch.object(ReceiptReader, "read", return_value=receipt):
        response = _post_upload(client, account, _barbora_file(), on)
    return response.content.decode()


@pytest.fixture(scope="module")
def barbora_receipt():
    return ReceiptReader.read(BARBORA)


@pytest.fixture
def account():
    return AccountFactory()


@pytest.fixture
def foreign_account(second_user):
    # the factory gets or creates an account by title alone
    return AccountFactory(title="Foreign account", journal=second_user.journal)


@pytest.fixture
def pieno():
    return ExpenseNameFactory(title="Pieno produktai", parent=ExpenseTypeFactory())


def _jogurt_row(name, **overrides):
    return {
        "title": "Naturalus jogurtas VILVI",
        "price": "5,00",
        "expense_type": name.parent.pk,
        "expense_name": name.pk,
        "keyword": "jogurt",
    } | overrides


def _post_save(client, rows, account, on=UPLOAD_DATE, **receipt_overrides):
    return client.post(
        reverse("expenses:import_save"),
        data=_save_data(rows, account, on, **receipt_overrides),
    )


def test_import_get_anonymous_redirects_to_login(client):
    url = reverse("expenses:import")
    response = client.get(url)

    assert response.status_code == 302


def test_import_get_200_renders_upload_form(main_user, client_logged):
    url = reverse("expenses:import")
    response = client_logged.get(url)

    text = response.content.decode()
    assert response.status_code == 200
    assert re.search(r'<link rel="stylesheet" href="[^"]*paper\.min\.css">', text)
    assert '<div class="paper-skin">' in text
    assert re.search(r'<div class="import-upload">\s*<div>\s*<label', text)
    assert re.search(r'<input type="file" name="pdf"[^>]*class="visually-hidden"', text)
    assert re.search(
        r'<span class="file-input__button">Pasirinkti failą</span>\s*'
        r'<span class="file-input__name" data-empty="Failas nepasirinktas"',
        text,
    )


def _non_pdf(tmp_path, mocker):
    return _upload("lydrastis.txt", b"x", "text/plain")


def _unrecognised_pdf(tmp_path, mocker):
    path = table_pdf(
        tmp_path / "unknown.pdf",
        text_above="UNKNOWN SHOP",
        header=("Item", "Qty", "Sum"),
        rows=[("Apple", "2 vnt.", "1,20")],
    )
    return _upload("unknown.pdf", path.read_bytes())


def _unreadable_receipt(tmp_path, mocker):
    mocker.patch.object(ReceiptReader, "read", side_effect=UnreadableReceiptTextError)
    return _barbora_file()


def _receipt_with_no_lines(tmp_path, mocker):
    mocker.patch.object(reader, "PARSERS", (TextReceiptParser(EMPTY_TEXT_LAYOUT),))
    path = empty_text_receipt_pdf(tmp_path / "empty.pdf")
    return _upload("empty.pdf", path.read_bytes())


def _corrupt_pdf(tmp_path, mocker):
    return _upload("notes.pdf", b"hello, not a pdf")


@pytest.mark.parametrize(
    "make_file, message",
    [
        pytest.param(_non_pdf, "Galima importuoti tik PDF failus.", id="non_pdf"),
        pytest.param(
            _unrecognised_pdf,
            "Šis PDF nėra palaikomos parduotuvės čekis.",
            id="unrecognised_pdf",
        ),
        pytest.param(
            _unreadable_receipt, "Čekio nepavyko nuskaityti.", id="unreadable_receipt"
        ),
        pytest.param(
            _receipt_with_no_lines, "Čekio nepavyko nuskaityti.", id="no_lines"
        ),
        pytest.param(_corrupt_pdf, "Čekio nepavyko nuskaityti.", id="corrupt_pdf"),
    ],
)
def test_import_post_unreadable_file_error(
    client_logged, account, tmp_path, mocker, make_file, message
):
    response = _post_upload(client_logged, account, make_file(tmp_path, mocker))

    text = response.content.decode()
    assert response.status_code == 200
    assert re.search(
        r'<div class="file-input"[^>]*>(?:(?!</div>).)*</div>\s*'
        rf'<div class="invalid-feedback">{message}</div>',
        text,
        re.DOTALL,
    )
    assert not re.search(r'<input[^>]*name="form-0-title"', text)


def test_import_post_fixture_29_rows(client_logged, account):
    response = _post_upload(client_logged, account, _barbora_file(), REVIEW_DATE)

    assert response.status_code == 200
    assert 'name="form-TOTAL_FORMS" value="29"' in response.content.decode()


def test_import_post_kg_line_amount_is_one(client_logged, account, barbora_receipt):
    kg_index = next(
        i
        for i, line in enumerate(barbora_receipt.lines)
        if line.amount == 1 and line.price == 280
    )

    text = _post_review(client_logged, account, barbora_receipt, REVIEW_DATE)

    assert f'name="form-{kg_index}-amount" value="1"' in text


def test_import_post_jogurt_keyword_prefills_row(
    main_user, client_logged, account, pieno, barbora_receipt
):
    ExpenseKeywordFactory(
        journal=main_user.journal, keyword="jogurt", expense_name=pieno
    )

    jogurt_index = next(
        i
        for i, line in enumerate(barbora_receipt.lines)
        if "jogurt" in line.title.casefold()
    )

    text = _post_review(client_logged, account, barbora_receipt, REVIEW_DATE)

    prefix = f"form-{jogurt_index}"
    expense_type = _select(text, f"{prefix}-expense_type")
    expense_name = _select(text, f"{prefix}-expense_name")
    assert _is_selected(expense_type, pieno.parent.pk)
    assert _is_selected(expense_name, pieno.pk)
    assert f'name="{prefix}-keyword" value="jogurt"' in text


def test_import_post_unmatched_row_blank_option_selected(client_logged, account):
    text = _post_review(client_logged, account, _receipt(total=500))

    assert re.search(
        r'<option value=""[^>]*\sselected\b', _select(text, "form-0-expense_type")
    )
    assert re.search(
        r'<option value=""[^>]*\sselected\b', _select(text, "form-0-expense_name")
    )


def test_import_post_every_skip_box_named_form_n_skip(client_logged, account):
    text = _post_review(client_logged, account, _n_line_receipt(3))

    assert 'name="form-0-skip"' in text
    assert 'name="form-2-skip"' in text


def _section(text, tag):
    match = re.search(rf"<{tag}>.*?</{tag}>", text, re.DOTALL)
    assert match, f"no <{tag}> in the response"
    return match.group(0)


def _select(text, name):
    match = re.search(rf'<select name="{name}".*?</select>', text, re.DOTALL)
    assert match, f"no select {name} in the response"
    return match.group(0)


def _is_selected(select, pk):
    return re.search(rf'<option value="{pk}"[^>]*\sselected\b', select) is not None


@pytest.mark.parametrize(
    "receipt, radios",
    [
        pytest.param(_shop_money_receipt(), 2, id="shop_money"),
        pytest.param(_receipt(total=500, shop_money=0), 0, id="no_shop_money"),
    ],
)
def test_import_post_shop_money_radios_only_when_positive(
    client_logged, account, receipt, radios
):
    text = _post_review(client_logged, account, receipt)

    radio = '<input type="radio" class="form-check-input" name="shop_money_line"'
    assert text.count(radio) == radios
    assert text.count('type="radio"') == radios
    assert 'name="shop_money_line"' in text
    assert 'name="form-0-shop_money_line"' not in text


@pytest.mark.parametrize(
    "total, warning",
    [
        pytest.param(999, '<p :hidden="!disagree">', id="disagreeing"),
        pytest.param(500, '<p :hidden="!disagree" hidden>', id="agreeing"),
    ],
)
def test_import_post_totals_warning(client_logged, account, total, warning):
    text = _post_review(client_logged, account, _receipt(total=total))

    assert f"{warning}Sumos nesutampa" in text


def _tfoot_rows(text):
    tfoot = _section(text, "tfoot")
    return re.findall(r"<tr class=\"main__total\">.*?</tr>", tfoot, re.DOTALL)


@pytest.mark.parametrize(
    "receipt, text_center_count, labels, colspan, row_count",
    [
        pytest.param(
            _receipt(total=500),
            1,
            ["Eilučių suma", "Čekio suma"],
            'colspan="3"',
            2,
            id="without_shop_money",
        ),
        pytest.param(
            _shop_money_receipt(),
            2,
            ["Eilučių suma", "Čekio suma", "Parduotuvės pinigai"],
            'colspan="4"',
            3,
            id="with_shop_money",
        ),
    ],
)
def test_import_review_table_follows_shop_money(
    client_logged, account, receipt, text_center_count, labels, colspan, row_count
):
    text = _post_review(client_logged, account, receipt)
    thead = _section(text, "thead")
    tfoot = _section(text, "tfoot")
    rows = _tfoot_rows(text)

    assert thead.count('class="text-left"') == 4
    assert thead.count('class="text-center"') == text_center_count
    assert "<th>Kiekis</th>" in thead
    assert "<th>Kaina</th>" in thead
    assert (
        re.findall(r'<tr class="main__total">\s*<td colspan="3">(.*?)</td>', tfoot)
        == labels
    )
    assert "&middot;" not in tfoot
    assert "·" not in tfoot
    assert len(rows) == row_count
    for row in rows:
        cells = re.findall(r"<td[^>]*>", row)
        assert len(cells) == 3
        assert cells[1] == '<td class="main__figure">'
        assert colspan in cells[-1]
    assert "<td></td>" not in tfoot


def test_import_post_query_count_equal_for_2_and_6_lines(client_logged, account):
    rendered = {}

    def post(n):
        rendered[n] = _post_review(
            client_logged, account, _n_line_receipt(n), REVIEW_DATE
        )

    two = count_queries(lambda: post(2))
    six = count_queries(lambda: post(6))

    assert 'name="form-TOTAL_FORMS" value="6"' in rendered[6]
    assert two == six


def test_import_save_valid_creates_expenses_and_redirects(
    client_logged, account, pieno
):
    duona = ExpenseNameFactory(title="Duona", parent=pieno.parent)

    response = _post_save(
        client_logged,
        [
            _jogurt_row(pieno),
            _jogurt_row(duona, title="Juoda duona", price="3,00", keyword="duon"),
        ],
        account,
        total="800",
        on=date(1998, 3, 5),
    )

    assert response.status_code == 200
    assert response["HX-Redirect"] == "/expenses/data/3/"
    assert [(e.expense_name, e.price) for e in Expense.objects.order_by("pk")] == [
        (pieno, 500),
        (duona, 300),
    ]
    assert ExpenseKeyword.objects.filter(keyword="jogurt", expense_name=pieno).exists()
    assert ExpenseKeyword.objects.filter(keyword="duon", expense_name=duona).exists()


def test_import_save_invalid_nothing_saved_names_intact(client_logged, account, pieno):
    # a missing required field on a non-skipped row
    response = _post_save(client_logged, [_jogurt_row(pieno, title="")], account)

    assert response.status_code == 200
    assert Expense.objects.count() == 0
    text = response.content.decode()
    assert _is_selected(_select(text, "form-0-expense_name"), pieno.pk)
    assert '<div class="invalid-feedback">' in _section(text, "tbody")


@pytest.mark.parametrize(
    "tamper, pattern",
    [
        pytest.param(
            "account",
            # a form-wide error: it renders first in the form, after the csrf token
            r'name="csrfmiddlewaretoken" value="[^"]*">\s*'
            r'<div class="invalid-feedback">Pasirinkite tinkamą reikšmę',
            id="account",
        ),
        pytest.param(
            "shop_money_line",
            r'<div class="invalid-feedback">'
            "Parduotuvės pinigų eilutės šiame čekyje nėra.",
            id="shop_money_line_out_of_range",
        ),
        pytest.param(
            "expense_type",
            r'<select name="form-0-expense_type"[^>]*>(?:(?!</td>).)*</select>\s*'
            r'<div class="invalid-feedback">'
            "Pasirinkite tinkamą reikšmę. Parinkta reikšmė nėra galima.",
            id="expense_type",
        ),
    ],
)
def test_import_save_tampered_input_is_refused(
    client_logged, second_user, account, foreign_account, pieno, tamper, pattern
):
    foreign_type = ExpenseTypeFactory(title="Foreign type", journal=second_user.journal)
    foreign_name = ExpenseNameFactory(title="Foreign name", parent=foreign_type)
    posts = {
        "account": ([_jogurt_row(pieno)], foreign_account, {}),
        "shop_money_line": (
            [_jogurt_row(pieno)],
            account,
            {"shop_money": "100", "shop_money_line": "5"},
        ),
        "expense_type": ([_jogurt_row(foreign_name)], account, {}),
    }
    rows, posted_account, overrides = posts[tamper]

    response = _post_save(client_logged, rows, posted_account, **overrides)

    assert response.status_code == 200
    assert Expense.objects.count() == 0
    assert re.search(pattern, response.content.decode(), re.DOTALL)


def test_import_save_tampered_account_still_shows_shop_money_radios(
    client_logged, foreign_account, pieno
):
    response = _post_save(
        client_logged,
        [_jogurt_row(pieno)],
        foreign_account,
        shop_money="100",
        shop_money_line="0",
    )

    assert response.status_code == 200
    assert Expense.objects.count() == 0
    text = response.content.decode()
    radio = '<input type="radio" class="form-check-input" name="shop_money_line"'
    assert radio in text
    assert re.search(r'name="shop_money_line" value="0"[^>]*\bchecked>', text)


def _n_rows(n, run, price="5,00"):
    rows = []
    for i in range(n):
        t = ExpenseTypeFactory(title=f"{run}-T{i}")
        name = ExpenseNameFactory(title=f"{run}-N{i}", parent=t)
        rows.append(
            _jogurt_row(
                name,
                title=f"Product {run}{i} kw{run}{i}",
                price=price,
                keyword=f"kw{run}{i}",
            )
        )
    return rows


def _save_queries(client, account, n, price, saved):
    rows = _n_rows(n, run=f"q{n}", price=price)
    responses = []

    queries = count_queries(lambda: responses.append(_post_save(client, rows, account)))

    assert responses[0].status_code == 200
    assert Expense.objects.count() == saved
    return queries


@pytest.mark.parametrize(
    "price, saved_after_2, saved_after_6",
    [
        pytest.param("0", 0, 0, id="invalid"),
        pytest.param("5,00", 2, 8, id="valid"),
    ],
)
def test_import_save_query_count_equal_for_2_and_6_lines(
    client_logged, account, price, saved_after_2, saved_after_6
):
    two = _save_queries(client_logged, account, 2, price, saved_after_2)
    six = _save_queries(client_logged, account, 6, price, saved_after_6)

    assert two == six


def test_import_review_row_error_colspan_with_shop_money(client_logged, account):
    response = _post_save(
        client_logged, [{"skip": "on"}], account, shop_money="100", shop_money_line="0"
    )

    text = response.content.decode()
    assert "Parduotuvės pinigų negalima priskirti praleistai eilutei." in text
    match = re.search(
        r'<td colspan="(\d+)">\s*<div class="invalid-feedback">'
        r"Parduotuvės pinigų negalima priskirti praleistai eilutei\.",
        text,
    )
    assert match is not None
    assert match.group(1) == "8"


def test_import_review_row_error_colspan_without_shop_money(main_user, account, pieno):
    data = _save_data([_jogurt_row(pieno)], account)

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
