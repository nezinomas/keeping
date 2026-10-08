from dataclasses import FrozenInstanceError

import pytest

from ...receipts.receipt import Receipt, ReceiptLine


def test_receipt_line_is_frozen():
    line = ReceiptLine(title="Bananai", amount=1, price=218, is_deposit=False)

    with pytest.raises(FrozenInstanceError):
        line.price = 1

    assert line.title == "Bananai"
    assert line.amount == 1
    assert line.price == 218
    assert line.is_deposit is False


def test_lines_total_sums_line_prices():
    lines = (
        ReceiptLine(title="A", amount=1, price=100, is_deposit=False),
        ReceiptLine(title="B", amount=1, price=200, is_deposit=False),
    )
    receipt = Receipt(lines=lines, total=300)

    assert receipt.lines_total == 300


@pytest.mark.parametrize(
    "prices,total,shop_money,expected",
    [
        pytest.param((7135,), 7135, 0, True, id="matches_total"),
        pytest.param((7134,), 7135, 0, False, id="one_cent_off"),
        pytest.param((979, 578), 1451, 106, True, id="shop_money_makes_up_the_gap"),
    ],
)
def test_agrees_compares_lines_total_less_shop_money_with_total(
    prices, total, shop_money, expected
):
    lines = tuple(
        ReceiptLine(title="A", amount=1, price=price, is_deposit=False)
        for price in prices
    )
    receipt = Receipt(lines=lines, total=total, shop_money=shop_money)

    assert receipt.lines_total == sum(prices)
    assert receipt.agrees is expected


def test_shop_money_defaults_to_zero():
    lines = (ReceiptLine(title="A", amount=1, price=100, is_deposit=False),)
    receipt = Receipt(lines=lines, total=100)

    assert receipt.shop_money == 0
