import re
from dataclasses import dataclass

import pdfplumber

from . import converters
from .errors import UnreadableReceiptTextError
from .layout import TextLayout
from .receipt import Receipt, ReceiptLine

_PRICED_LINE = re.compile(r"^(.*) (-?\d+,\d{2}) ([A-Z])$")
_TRAILING_MONEY = re.compile(r"(-?\d+,\d{2})(?: [A-Z])?$")


@dataclass
class _Product:
    title: str
    price: int
    amount: int = 1


@dataclass(frozen=True)
class TextReceiptParser:
    layout: TextLayout

    def recognises(self, text: str) -> bool:
        return self.layout.marker in text

    def parse(self, document: pdfplumber.PDF) -> Receipt:
        pages = [converters.lines(page.extract_text()) for page in document.pages]
        at = self._page_of(pages, self.layout.lines_start)
        page = pages[at]
        start = self._index_after(page, self.layout.lines_start)
        # the lines must end on the page they start on: a page break brings the
        # PDF's own footer and header between them, and those are not lines
        end = self._index_of_prefix(page, start, self.layout.lines_end)
        products = self._products(list(page[start:end]))
        tail = [*page[end:], *(line for later in pages[at + 1 :] for line in later)]
        return Receipt(
            lines=tuple(self._receipt_line(product) for product in products),
            total=self._total(tail),
            shop_money=self._shop_money(tail),
        )

    def _page_of(self, pages: list[tuple[str, ...]], marker: str) -> int:
        for index, page in enumerate(pages):
            if any(marker in line for line in page):
                return index
        raise UnreadableReceiptTextError(marker)

    def _index_after(self, lines: tuple[str, ...], marker: str) -> int:
        for index, line in enumerate(lines):
            if marker in line:
                return index + 1
        raise UnreadableReceiptTextError(marker)

    def _index_of_prefix(self, lines: tuple[str, ...], start: int, prefix: str) -> int:
        for index in range(start, len(lines)):
            if lines[index].startswith(prefix):
                return index
        raise UnreadableReceiptTextError(prefix)

    def _products(self, region: list[str]) -> list[_Product]:
        products: list[_Product] = []
        pending_title = ""
        for line in region:
            if self._is_amount_line(line):
                pending_title = self._apply_amount(products, pending_title, line)
            elif line.startswith(self.layout.item_discount_prefixes):
                pending_title = self._apply_discount(products, pending_title, line)
            else:
                pending_title = self._apply_text(products, pending_title, line)
        if pending_title:
            raise UnreadableReceiptTextError(pending_title)
        return products

    def _is_amount_line(self, line: str) -> bool:
        before, separator, _ = line.partition(self.layout.amount_separator)
        return bool(separator) and converters.is_money(before)

    def _apply_amount(
        self, products: list[_Product], pending_title: str, line: str
    ) -> str:
        if pending_title or not products:
            raise UnreadableReceiptTextError(line)
        _, amount_text = line.split(self.layout.amount_separator, 1)
        products[-1].amount = converters.amount(amount_text, self.layout.unit_words)
        return ""

    def _apply_discount(
        self, products: list[_Product], pending_title: str, line: str
    ) -> str:
        if pending_title or not products:
            raise UnreadableReceiptTextError(line)
        _, money_text = self._priced(line)
        products[-1].price += converters.money(money_text)
        return ""

    def _apply_text(
        self, products: list[_Product], pending_title: str, line: str
    ) -> str:
        match = _PRICED_LINE.match(line)
        if match is None:
            return self._joined(pending_title, line)
        title_part, money_text = self._checked_vat(match)
        title = self._joined(pending_title, title_part)
        products.append(_Product(title=title, price=converters.money(money_text)))
        return ""

    def _priced(self, line: str) -> tuple[str, str]:
        match = _PRICED_LINE.match(line)
        if match is None:
            raise UnreadableReceiptTextError(line)
        return self._checked_vat(match)

    def _checked_vat(self, match: re.Match) -> tuple[str, str]:
        title_part, money_text, vat_class = match.groups()
        if vat_class not in self.layout.vat_classes:
            raise UnreadableReceiptTextError(match.string)
        return title_part, money_text

    def _joined(self, pending_title: str, text: str) -> str:
        if pending_title:
            return f"{pending_title} {text}"
        return text

    def _receipt_line(self, product: _Product) -> ReceiptLine:
        return ReceiptLine(
            title=product.title,
            amount=product.amount,
            price=product.price,
            is_deposit=converters.is_deposit(product.title, self.layout.deposit_words),
        )

    def _total(self, tail: list[str]) -> int:
        line = self._labelled(tail, self.layout.total_label)
        if not line:
            raise UnreadableReceiptTextError(self.layout.total_label)
        return converters.money(self._trailing_money(line))

    def _shop_money(self, tail: list[str]) -> int:
        line = self._labelled(tail, self.layout.shop_money_label)
        if not line:
            return 0
        return -converters.money(self._trailing_money(line))

    def _labelled(self, tail: list[str], label: str) -> str:
        return next((line for line in tail if line.startswith(label)), "")

    def _trailing_money(self, line: str) -> str:
        match = _TRAILING_MONEY.search(line)
        if match is None:
            raise UnreadableReceiptTextError(line)
        return match.group(1)
