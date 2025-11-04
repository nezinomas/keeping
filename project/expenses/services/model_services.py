from typing import Optional, cast

from ...users.models import User
from ..managers import ExpenseNameQuerySet, ExpenseQuerySet, ExpenseTypeQuerySet
from ..models import Expense, ExpenseName, ExpenseType


class ExpenseTypeModelService:
    def __init__(
        self,
        user: User,
    ):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.user = user

    def related(self):
        return cast(ExpenseTypeQuerySet, ExpenseType.objects).related(self.user)

    def items(self):
        return cast(ExpenseTypeQuerySet, ExpenseType.objects).items(self.user)


class ExpenseNameModelService:
    def __init__(
        self,
        user: User,
    ):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.user = user

    def related(self):
        return cast(ExpenseNameQuerySet, ExpenseName.objects).related(self.user)

    def items(self):
        return cast(ExpenseNameQuerySet, ExpenseName.objects).items(self.user)

    def year(self, year: int):
        return cast(ExpenseNameQuerySet, ExpenseName.objects).year(self.user, year)

    def none(self):
        return ExpenseName.objects.none()


class ExpenseModelService:
    def __init__(self, user: User):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.user = user

    def related(self):
        return cast(ExpenseQuerySet, Expense.objects).related(self.user)

    def items(self):
        return cast(ExpenseQuerySet, Expense.objects).items(self.user)

    def sum_by_month(self, year: int):
        return cast(ExpenseQuerySet, Expense.objects).sum_by_month(self.user, year)

    def sum_by_month_and_type(self, year: int):
        return cast(ExpenseQuerySet, Expense.objects).sum_by_month_and_type(
            self.user, year
        )

    def sum_by_month_and_name(self, year: int):
        return cast(ExpenseQuerySet, Expense.objects).sum_by_month_and_name(
            self.user, year
        )

    def sum_by_day_and_type(self, year: int, month: int):
        return cast(ExpenseQuerySet, Expense.objects).sum_by_day_ant_type(
            self.user, year, month
        )

    def sum_by_year(self):
        return cast(ExpenseQuerySet, Expense.objects).sum_by_year(self.user)

    def sum_by_year_type(self, expense_type: Optional[list[int]] = None):
        return cast(ExpenseQuerySet, Expense.objects).sum_by_year_type(
            self.user, expense_type
        )

    def sum_by_year_name(self, expense_name: Optional[list[int]] = None):
        return cast(ExpenseQuerySet, Expense.objects).sum_by_year_name(
            self.user, expense_name
        )

    def last_months(self, months: int):
        return cast(ExpenseQuerySet, Expense.objects).last_months(self.user, months)
