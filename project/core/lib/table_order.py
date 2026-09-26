from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Column:
    key: str
    descending: bool = False


@dataclass(frozen=True)
class Ordered[T]:
    rows: list[T]
    active: str


@dataclass(frozen=True)
class TableOrder:
    columns: tuple[Column, ...]
    default: str

    def sort[T](
        self,
        order: str,
        rows: Sequence[T],
        values: Callable[[T], Mapping[str, Any]],
    ) -> Ordered[T]:
        column = self._column(order)
        present = [row for row in rows if column.key in values(row)]
        absent = [row for row in rows if column.key not in values(row)]
        present.sort(key=lambda row: values(row)[column.key], reverse=column.descending)

        return Ordered(rows=present + absent, active=column.key)

    def _column(self, order: str) -> Column:
        columns = {column.key: column for column in self.columns}
        return columns.get(order, columns[self.default])
