from ...receipts.reader import ReceiptReader
from .pdfs import FIXTURES


def test_barbora_promotion_reads_38_lines_that_agree():
    receipt = ReceiptReader.read(FIXTURES / "barbora_promotion.pdf")

    assert len(receipt.lines) == 38
    assert receipt.total == 10111
    assert receipt.agrees


def test_barbora_promotion_gives_the_price_to_the_row_below():
    receipt = ReceiptReader.read(FIXTURES / "barbora_promotion.pdf")

    titles = [line.title for line in receipt.lines]
    line = next(
        line
        for line in receipt.lines
        if line.title.startswith(
            "KĖDAINIŲ KONSERVŲ FABRIKO marinuoti agurkai su ąžuolų lapais, 660 g"
        )
    )

    assert line.amount == 2
    assert line.price == 349
    assert not any(title.startswith("4 grūdų trapučiai") for title in titles)


def test_barbora_substitute_reads_38_lines_that_agree():
    receipt = ReceiptReader.read(FIXTURES / "barbora_substitute.pdf")

    assert len(receipt.lines) == 38
    assert receipt.total == 10215
    assert receipt.agrees


def test_barbora_substitute_drops_the_original_and_keeps_the_substitute():
    receipt = ReceiptReader.read(FIXTURES / "barbora_substitute.pdf")

    titles = [line.title for line in receipt.lines]
    line = next(
        line for line in receipt.lines if line.title == "Romaninės salotos, 1 vnt."
    )

    assert line.price == 139
    assert line.amount == 1
    assert not any(title.startswith("Gūžinės salotos") for title in titles)


def test_barbora_two_pages_reads_47_lines_that_agree():
    receipt = ReceiptReader.read(FIXTURES / "barbora_two_pages.pdf")

    assert len(receipt.lines) == 47
    assert receipt.total == 11789
    assert receipt.agrees


def test_barbora_two_pages_continues_the_product_table_onto_the_second_page():
    receipt = ReceiptReader.read(FIXTURES / "barbora_two_pages.pdf")

    line = receipt.lines[39]

    assert line.title == "Konservuoti kukurūzai WELL DONE, 150 g"
    assert line.amount == 3
    assert line.price == 207
