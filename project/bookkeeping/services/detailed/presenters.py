from django.utils.text import slugify
from django.utils.translation import gettext as _

from ....expenses.services.model_services import ExpenseTypeModelService
from ....users.models import User
from .builders import DetailedTableBuilder
from .dtos import DetailedDto
from .providers import DetailedDataProvider


class DetailedContextPresenter:
    """Formats a TableBuilder into the exact dictionary structure required by the UI."""

    @staticmethod
    def build(
        title: str, url_title: str, dto: DetailedDto, year: int, order: str
    ) -> dict:
        if not dto.data:
            return {}

        builder = DetailedTableBuilder(dto, year, order)

        return {
            "title": title,
            "url_title": url_title,
            "data": builder.table,
            "total": builder.total_row,
        }


def load_service(user: User, category: str = "all_data", order: str = "") -> list[dict]:
    year = user.year
    provider = DetailedDataProvider(user)
    contexts = []

    # 1. Assemble categories
    match category:
        case "all_data":
            categories = [
                (_("Incomes"), "income", provider.get_incomes()),
                (_("Savings"), "saving", provider.get_savings()),
            ]
            categories.extend(
                (f"{_('Expenses')} / {title}", slugify(title), dto)
                for title, dto in provider.get_expenses().items()
                if dto.data
            )

        case "income":
            categories = [(_("Incomes"), "income", provider.get_incomes())]

        case "saving":
            categories = [(_("Savings"), "saving", provider.get_savings())]

        case _:
            expense_type = (
                ExpenseTypeModelService(user).objects.filter(slug=category).first()
            )
            if not expense_type:
                return []

            title = f"{_('Expenses')} / {expense_type.title}"
            categories = [(title, category, provider.get_expense(expense_type.slug))]

    # 2. Build contexts
    for title, url_title, dto in categories:
        if not all((title, url_title, dto.data)):
            continue

        if context := DetailedContextPresenter.build(
            title=title, url_title=url_title, dto=dto, year=year, order=order
        ):
            contexts.append(context)

    return contexts
