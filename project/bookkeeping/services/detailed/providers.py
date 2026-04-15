from collections import defaultdict

from ....expenses.services.model_services import ExpenseModelService
from ....incomes.services.model_services import IncomeModelService
from ....savings.services.model_services import SavingModelService
from ....users.models import User
from .dtos import DetailedDto


class DetailedDataProvider:
    """Single point of truth for fetching detailed data from the database."""

    def __init__(self, user: User):
        self.user = user
        self.year = user.year

    def get_incomes(self) -> DetailedDto:
        return DetailedDto(
            data=list(IncomeModelService(self.user).sum_by_month_and_type(self.year))
        )

    def get_savings(self) -> DetailedDto:
        return DetailedDto(
            data=list(SavingModelService(self.user).sum_by_month_and_type(self.year))
        )

    def get_expenses(self) -> dict[str, DetailedDto]:
        """Returns a dictionary mapping expense categories to their respective DTOs."""
        qs = ExpenseModelService(self.user).sum_by_month_and_name(self.year)

        grouped_data = defaultdict(list)
        for record in qs:
            group_key = record.pop("type_title")
            grouped_data[group_key].append(record)

        return {title: DetailedDto(data=data) for title, data in grouped_data.items()}

    def get_expense(self, category_slug: str) -> DetailedDto:
        """Fetches a single expense category filtered directly at the DB level."""
        qs = (
            ExpenseModelService(self.user)
            .sum_by_month_and_name(self.year)
            .filter(expense_type__slug=category_slug)
        )
        return DetailedDto(data=list(qs))
