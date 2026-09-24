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
        for rows in self._tables(document):
            if self._carries_columns(rows[0]):
                return self._receipt(
                    rows, ColumnIndexes.of(rows[0], self.layout.columns)
                )
        raise UnreadableReceiptTextError(self.layout.marker)

    def _tables(self, document: pdfplumber.PDF) -> Iterator[list[Row]]:
        for page in document.pages:
            for table in page.extract_tables():
                if table:
                    yield [[converters.cell(value) for value in row] for row in table]

    def _carries_columns(self, header: Row) -> bool:
        return all(name in header for name in self.layout.columns.names)

    def _receipt(self, rows: list[Row], at: ColumnIndexes) -> Receipt:
        return Receipt(
            lines=tuple(self._product_lines(rows, at)),
            total=self._total(rows, at),
        )

    def _product_lines(
        self, rows: list[Row], at: ColumnIndexes
    ) -> Iterator[ReceiptLine]:
        body = rows[1:]
        end = next((n for n, row in enumerate(body) if row[at.amount] == ""), len(body))
        # a product row after the first blank amount means a line would be lost
        if any(row[at.amount] for row in body[end:]):
            raise UnreadableReceiptTextError(self.layout.columns.amount)
        for row in body[:end]:
            yield self._line(row, at)

    def _line(self, row: Row, at: ColumnIndexes) -> ReceiptLine:
        title = row[at.title]
        return ReceiptLine(
            title=title,
            amount=converters.amount(row[at.amount], self.layout.unit_words),
            price=converters.money(row[at.price]),
            is_deposit=converters.is_deposit(title, self.layout.deposit_words),
        )

    def _total(self, rows: list[Row], at: ColumnIndexes) -> int:
        for row in rows[1:]:
            if row[at.title] == self.layout.total_label:
                return converters.money(row[at.price])
        raise UnreadableReceiptTextError(self.layout.total_label)
