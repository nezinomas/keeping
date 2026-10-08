import re

import pdfplumber
import pytest

from ...receipts.layouts import BARBORA
from ...receipts.table_parser import TableReceiptParser
from .pdfs import FIXTURES

FIXTURE = FIXTURES / "barbora.pdf"

_SUMMARY_TITLES = (
    "Apmokestinama 21,00%",
    "PVM suma 21,00%",
    "Depozitas",
    "Bendra suma",
    "Jums priklausantis lipdukų kiekis",
)


def _receipt():
    with pdfplumber.open(FIXTURE) as document:
        return TableReceiptParser(BARBORA).parse(document)


def test_barbora_parses_29_lines():
    receipt = _receipt()

    assert len(receipt.lines) == 29


def test_barbora_lines_total_agrees_with_total():
    receipt = _receipt()

    assert receipt.total == 7135
    assert receipt.lines_total == 7135
    assert receipt.agrees


def test_barbora_line_1_is_the_whole_wrapped_title():
    receipt = _receipt()

    assert receipt.lines[0].title == (
        "Ekologiškas šaltai spaustas moliūgų sėklų aliejus BIONATURAL, 250 ml"
    )


def test_barbora_line_19_ends_with_weight():
    receipt = _receipt()

    assert receipt.lines[18].title.endswith(", 1 kg")


def test_barbora_titles_have_no_ean_digits_or_ellipsis():
    receipt = _receipt()

    for line in receipt.lines:
        assert "..." not in line.title
        assert re.search(r"\d{5,}", line.title) is None


@pytest.mark.parametrize(
    "index,amount,price",
    [
        pytest.param(1, 1, 280, id="line_2_weighed_product"),
        pytest.param(19, 6, 690, id="line_20_piece_product"),
        pytest.param(28, 1, 269, id="line_29_packaging_fee"),
    ],
)
def test_barbora_line_amount_and_price(index, amount, price):
    receipt = _receipt()

    assert receipt.lines[index].amount == amount
    assert receipt.lines[index].price == price


def test_barbora_only_lines_11_and_17_are_deposit_lines():
    receipt = _receipt()

    deposit_indexes = [i for i, line in enumerate(receipt.lines) if line.is_deposit]

    assert deposit_indexes == [10, 16]
    assert receipt.lines[10].price == 40
    assert receipt.lines[16].price == 30


def test_barbora_summary_rows_are_not_lines():
    receipt = _receipt()

    titles = [line.title for line in receipt.lines]

    for summary_title in _SUMMARY_TITLES:
        assert summary_title not in titles
