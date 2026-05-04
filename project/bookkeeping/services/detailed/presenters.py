from django.utils.text import slugify
from django.utils.translation import gettext as _

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


def load_full_service(user: User) -> list:
    year = user.year
    provider = DetailedDataProvider(user)
    contexts = []

    # Assemble all categories
    categories = [
        (_("Incomes"), "income", provider.get_incomes()),
        (_("Savings"), "saving", provider.get_savings()),
    ]

    for title, dto in provider.get_expenses().items():
        if not dto.data:
            continue
        categories.append((f"{_('Expenses')} / {title}", slugify(title), dto))

    # Build contexts
    for title, url_title, dto in categories:
        if context := DetailedContextPresenter.build(
            title=title, url_title=url_title, dto=dto, year=year, order=""
        ):
            contexts.append(context)

    return contexts


def load_partial_service(user: User, category: str, order: str) -> dict:
    """Returns ONLY the specific category requested for dynamic HTMX sorting."""
    year = user.year
    provider = DetailedDataProvider(user)

    match category:
        case "income":
            title = _("Incomes")
            dto = provider.get_incomes()
        case "saving":
            title = _("Savings")
            dto = provider.get_savings()
        case _:
            title = f"{_('Expenses')} / {category.replace('-', ' ').title()}"
            dto = provider.get_expense(category_slug=category)

    return DetailedContextPresenter.build(
        title=title, url_title=category, dto=dto, year=year, order=order
    )
