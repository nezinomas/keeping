from dataclasses import dataclass, replace
from datetime import date
from typing import TYPE_CHECKING

from django.db import transaction

from ...core.signals import accounts_signal, update_journal_first_record
from ..keywords import normalise_keyword
from ..models import Expense, ExpenseKeyword
from ..receipts.receipt import ReceiptLine

if TYPE_CHECKING:
    from ...accounts.models import Account
    from ...journals.models import Journal
    from ..models import ExpenseName


@dataclass(frozen=True)
class ReviewedLine:
    line: ReceiptLine
    expense_name: "ExpenseName"
    keyword: str
    carries_shop_money: bool


@dataclass
class ShopMoney:
    @classmethod
    def apply(
        cls, lines: tuple[ReviewedLine, ...], amount: int
    ) -> tuple[ReviewedLine, ...]:
        if amount == 0:
            return lines

        return tuple(
            replace(
                reviewed,
                line=replace(reviewed.line, price=reviewed.line.price - amount),
            )
            if reviewed.carries_shop_money
            else reviewed
            for reviewed in lines
        )


@dataclass(frozen=True)
class ExpenseGroup:
    expense_name: "ExpenseName"
    price: int
    quantity: int


@dataclass
class ExpenseGroups:
    @classmethod
    def build(cls, lines: tuple[ReviewedLine, ...]) -> list[ExpenseGroup]:
        by_name: dict[ExpenseName, list[ReviewedLine]] = {}
        for reviewed in lines:
            by_name.setdefault(reviewed.expense_name, []).append(reviewed)

        return [cls._group(name, rows) for name, rows in by_name.items()]

    @classmethod
    def _group(cls, expense_name, rows: list[ReviewedLine]) -> ExpenseGroup:
        price = sum(row.line.price for row in rows)
        quantity = sum(row.line.amount for row in rows if not row.line.is_deposit)
        if quantity == 0:
            quantity = 1

        return ExpenseGroup(expense_name=expense_name, price=price, quantity=quantity)


@dataclass
class ReceiptImport:
    @classmethod
    def save(
        cls,
        lines: tuple[ReviewedLine, ...],
        shop_money: int,
        date: date,
        account: "Account",
        journal: "Journal",
    ) -> list[Expense]:
        with transaction.atomic():
            reviewed = ShopMoney.apply(lines, shop_money)
            groups = ExpenseGroups.build(reviewed)

            expenses = Expense.objects.bulk_create(
                Expense(
                    date=date,
                    price=group.price,
                    quantity=group.quantity,
                    expense_type=group.expense_name.parent,
                    expense_name=group.expense_name,
                    account=account,
                    remark="",
                    exception=False,
                )
                for group in groups
            )

            if expenses:
                accounts_signal(sender=Expense, instance=expenses[0])
                update_journal_first_record(
                    sender=Expense, instance=expenses[0], created=True
                )

            cls._save_keywords(reviewed, journal)

        return expenses

    @classmethod
    def _save_keywords(cls, reviewed: tuple[ReviewedLine, ...], journal: "Journal"):
        # last choice wins: later lines overwrite earlier ones for the same keyword
        by_keyword = {normalise_keyword(rl.keyword): rl.expense_name for rl in reviewed}

        for keyword, expense_name in by_keyword.items():
            ExpenseKeyword.objects.update_or_create(
                journal=journal,
                keyword=keyword,
                defaults={"expense_name": expense_name},
            )
