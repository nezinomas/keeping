from ...receipts.receipt import Receipt, ReceiptLine


def test_receipt_line_is_frozen():
    line = ReceiptLine(title="Bananai", amount=1, price=218, is_deposit=False)

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


def test_agrees_when_lines_total_matches_total():
    lines = (ReceiptLine(title="A", amount=1, price=7135, is_deposit=False),)
    receipt = Receipt(lines=lines, total=7135)

    assert receipt.agrees is True


def test_agrees_false_when_lines_total_is_one_cent_off_and_no_exception():
    lines = (ReceiptLine(title="A", amount=1, price=7134, is_deposit=False),)
    receipt = Receipt(lines=lines, total=7135)

    assert receipt.agrees is False


def test_agrees_with_shop_money():
    lines = (
        ReceiptLine(title="A", amount=1, price=979, is_deposit=False),
        ReceiptLine(title="B", amount=1, price=578, is_deposit=False),
    )
    receipt = Receipt(lines=lines, total=1451, shop_money=106)

    assert receipt.lines_total == 1557
    assert receipt.agrees is True


def test_shop_money_defaults_to_zero():
    lines = (ReceiptLine(title="A", amount=1, price=100, is_deposit=False),)
    receipt = Receipt(lines=lines, total=100)

    assert receipt.shop_money == 0
