import pdfplumber

from ...receipts.layouts import MAXIMA
from ...receipts.receipt import ReceiptLine
from ...receipts.text_parser import TextReceiptParser
from .pdfs import FIXTURES

FIXTURE = FIXTURES / "maxima.pdf"


def _receipt():
    with pdfplumber.open(FIXTURE) as document:
        return TextReceiptParser(MAXIMA).parse(document)


def test_maxima_reads_seven_lines_in_order():
    receipt = _receipt()

    assert receipt.lines == (
        ReceiptLine(
            title="Biri VILVI varškė, 9 % rieb.",
            amount=1,
            price=395,
            is_deposit=False,
        ),
        ReceiptLine(
            title="Silpnai sūdyta LIETUVIŠKA silkių filė NORVELITA",
            amount=1,
            price=159,
            is_deposit=False,
        ),
        ReceiptLine(
            title="Kefyras VILVI, 2,5 % rieb.",
            amount=1,
            price=185,
            is_deposit=False,
        ),
        ReceiptLine(
            title="Valgomieji KARALIŠKI šokoladiniai ledai su pyrago",
            amount=1,
            price=679,
            is_deposit=False,
        ),
        ReceiptLine(
            title="Citrinos, 3-4 d. EUREKA, 1 kl.",
            amount=1,
            price=40,
            is_deposit=False,
        ),
        ReceiptLine(
            title="Bulvės LINKĖJIMAI IŠ KAIMO, 50-70 mm",
            amount=1,
            price=98,
            is_deposit=False,
        ),
        ReceiptLine(
            title="Vienkartinis plastikinis maišelis",
            amount=1,
            price=1,
            is_deposit=False,
        ),
    )


def test_maxima_totals_agree():
    receipt = _receipt()

    assert receipt.lines_total == 1557
    assert receipt.shop_money == 106
    assert receipt.total == 1451
    assert receipt.agrees


def _markdown_receipt():
    with pdfplumber.open(FIXTURES / "maxima_markdown.pdf") as document:
        return TextReceiptParser(MAXIMA).parse(document)


def test_maxima_markdown_reads_seven_lines_in_order():
    receipt = _markdown_receipt()

    assert receipt.lines == (
        ReceiptLine(
            title="Plombyras NYKŠTUKAS su šokoladu, sutirštinto pieno",
            amount=1,
            price=699,
            is_deposit=False,
        ),
        ReceiptLine(
            title="Sūris salotoms GRIKIOS, 45 % rieb. s. m.",
            amount=1,
            price=209,
            is_deposit=False,
        ),
        ReceiptLine(
            title="Lapinės salotos vazonėlyje",
            amount=1,
            price=79,
            is_deposit=False,
        ),
        ReceiptLine(
            title="Šviežiai raugti agurkai",
            amount=1,
            price=269,
            is_deposit=False,
        ),
        ReceiptLine(
            title="Citrinos, 3-4 d.",
            amount=1,
            price=41,
            is_deposit=False,
        ),
        ReceiptLine(
            title="Kriaušės GUYOT (60-70 mm)",
            amount=1,
            price=149,
            is_deposit=False,
        ),
        ReceiptLine(
            title="Vienkartinis plastikinis maišelis",
            amount=2,
            price=2,
            is_deposit=False,
        ),
    )


def test_maxima_markdown_totals_agree():
    receipt = _markdown_receipt()

    assert receipt.lines_total == 1448
    assert receipt.shop_money == 210
    assert receipt.total == 1238
    assert receipt.agrees
