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
