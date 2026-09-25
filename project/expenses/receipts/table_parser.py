from collections.abc import Iterator
from dataclasses import dataclass

import pdfplumber

from . import converters
from .errors import UnreadableReceiptTextError
from .layout import Columns, TableLayout
from .receipt import Receipt, ReceiptLine

Row = list[str]


@dataclass(frozen=True)
class ColumnIndexes:
    title: int
    amount: int
    price: int

    @classmethod
    def of(cls, header: Row, columns: Columns) -> "ColumnIndexes":
        return cls(*(header.index(name) for name in columns.names))


@dataclass(frozen=True)
class TableReceiptParser:
    layout: TableLayout

    def recognises(self, text: str) -> bool:
        return self.layout.marker in text

    def parse(self, document: pdfplumber.PDF) -> Receipt:
        tables = list(self._tables(document))
        for index, rows in enumerate(tables):
            if self._carries_columns(rows[0]):
                at = ColumnIndexes.of(rows[0], self.layout.columns)
                body = self._product_rows(tables, index)
                return Receipt(
                    lines=tuple(self._receipt_lines(body, at)),
                    total=self._total(tables),
                )
        raise UnreadableReceiptTextError(self.layout.marker)

    def _tables(self, document: pdfplumber.PDF) -> Iterator[list[Row]]:
        for page in document.pages:
            for table in page.extract_tables():
                if table:
                    yield [[converters.cell(value) for value in row] for row in table]

    def _carries_columns(self, header: Row) -> bool:
        return all(name in header for name in self.layout.columns.names)

    def _product_rows(self, tables: list[list[Row]], header_index: int) -> list[Row]:
        width = len(tables[header_index][0])
        rows = list(tables[header_index][1:])
        for later in tables[header_index + 1 :]:
            if len(later[0]) == width:
                rows.extend(later)
        return rows

    def _receipt_lines(self, body: list[Row], at: ColumnIndexes) -> list[ReceiptLine]:
        lines: list[ReceiptLine] = []
        rows = iter(body)
        for row in rows:
            if self._is_promotion(row):
                lines.append(self._promotion_line(row, rows, at))
                continue
            if row[at.amount] == "":
                break
            if row[at.amount] == "0":
                self._verify_not_collected(row, at)
                continue
            lines.append(self._line(row, at))
        # a product row after the first blank amount means a line would be lost
        if any(row[at.amount] for row in rows):
            raise UnreadableReceiptTextError(self.layout.columns.amount)
        return lines

    def _is_promotion(self, row: Row) -> bool:
        return self.layout.promotion_label in row

    def _promotion_line(
        self, promotion_row: Row, rows: Iterator[Row], at: ColumnIndexes
    ) -> ReceiptLine:
        try:
            product_row = next(rows)
        except StopIteration:
            raise UnreadableReceiptTextError(self.layout.promotion_label) from None
        if product_row[at.amount] in ("", "0") or product_row[at.price] != "":
            raise UnreadableReceiptTextError(self.layout.promotion_label)
        priced = [*product_row]
        priced[at.price] = promotion_row[at.price]
        return self._line(priced, at)

    def _verify_not_collected(self, row: Row, at: ColumnIndexes) -> None:
        if converters.money(row[at.price]) != 0:
            raise UnreadableReceiptTextError(row[at.price])

    def _line(self, row: Row, at: ColumnIndexes) -> ReceiptLine:
        title = row[at.title]
        return ReceiptLine(
            title=title,
            amount=converters.amount(row[at.amount], self.layout.unit_words),
            price=converters.money(row[at.price]),
            is_deposit=converters.is_deposit(title, self.layout.deposit_words),
        )

    def _total(self, tables: list[list[Row]]) -> int:
        for rows in tables:
            for row in rows:
                if self.layout.total_label in row:
                    return converters.money(self._last_non_empty(row))
        raise UnreadableReceiptTextError(self.layout.total_label)

    def _last_non_empty(self, row: Row) -> str:
        return next((value for value in reversed(row) if value), "")
