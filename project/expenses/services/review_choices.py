from dataclasses import dataclass

from ..models import ExpenseName, ExpenseType
from .model_services import ExpenseNameModelService, ExpenseTypeModelService


@dataclass(frozen=True)
class ReviewChoices:
    """The Expense types and Expense names one Review offers, loaded once."""

    types: tuple[ExpenseType, ...]
    names: tuple[ExpenseName, ...]

    @classmethod
    def load(cls, user, year: int) -> "ReviewChoices":
        types = tuple(ExpenseTypeModelService(user).items().prefetch_related(None))
        names = tuple(ExpenseNameModelService(user).year(year))

        return cls(types=types, names=names)

    def names_for(self, expense_type_pk: int) -> tuple[ExpenseName, ...]:
        return tuple(name for name in self.names if name.parent_id == expense_type_pk)
