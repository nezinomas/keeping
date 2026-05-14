from django.utils.text import slugify
from django.utils.translation import gettext as _

from ....users.models import User
from .builders import DetailedTableBuilder
from .dtos import DetailedDto
from .providers import DetailedDataProvider


def build_context(
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


def _get_categories(
    user: User, category: str, provider: DetailedDataProvider
) -> list[tuple[str, str, DetailedDto]]:
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
            return categories

        case "income":
            return [(_("Incomes"), "income", provider.get_incomes())]

        case "saving":
            return [(_("Savings"), "saving", provider.get_savings())]

        case _:
            expense_type = provider.get_expense_type(category)
            if not expense_type:
                return []

            title = f"{_('Expenses')} / {expense_type.title}"
            return [(title, category, provider.get_expense(expense_type.slug))]


def load_service(user: User, category: str = "all_data", order: str = "") -> list[dict]:
    provider = DetailedDataProvider(user)
    contexts = []

    categories = _get_categories(user, category, provider)

    for title, url_title, dto in categories:
        if context := build_context(
            title=title,
            url_title=url_title,
            dto=dto,
            year=user.year,
            order=order,
        ):
            contexts.append(context)

    return contexts
