from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..models import ExpenseKeyword, ExpenseName


@dataclass(frozen=True)
class Match:
    keyword: str
    expense_name: "ExpenseName"

    def initial(self) -> dict[str, Any]:
        return {
            "expense_type": self.expense_name.parent,
            "expense_name": self.expense_name,
            "keyword": self.keyword,
        }


@dataclass(frozen=True)
class NoMatch:
    def initial(self) -> dict[str, Any]:
        return {}


@dataclass
class KeywordMatcher:
    @classmethod
    def match(cls, title: str, keywords: Iterable["ExpenseKeyword"]) -> Match | NoMatch:
        folded_title = title.casefold()
        found = [k for k in keywords if k.keyword in folded_title]
        if not found:
            return NoMatch()

        best = min(
            found, key=lambda k: (-len(k.keyword), folded_title.index(k.keyword))
        )
        return Match(keyword=best.keyword, expense_name=best.expense_name)
