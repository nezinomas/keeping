from dataclasses import dataclass


@dataclass(frozen=True)
class ReceiptLine:
    title: str
    amount: int
    price: int
    is_deposit: bool


@dataclass(frozen=True)
class Receipt:
    lines: tuple[ReceiptLine, ...]
    total: int
    shop_money: int = 0

    @property
    def lines_total(self) -> int:
        return sum(line.price for line in self.lines)

    @property
    def agrees(self) -> bool:
        return self.lines_total == self.total + self.shop_money
