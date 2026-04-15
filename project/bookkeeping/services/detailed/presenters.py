from django.utils.text import slugify
from django.utils.translation import gettext as _

from ....users.models import User
from .builders import DetailedTableBuilder
from .dtos import DetailedDto
from .providers import DetailedDataProvider


class DetailedContextPresenter:
    """Formats a TableBuilder into the exact dictionary structure required by the UI."""
    @staticmethod
    def build(title: str, url_title: str, dto: DetailedDto, year: int, order: str) -> dict:
        builder = DetailedTableBuilder(dto, year, order)
        return {
            "title": title,
            "url_title": url_title,
            "data": builder.table,
            "total": builder.total_row,
        }


def load_full_service(user: User) -> dict:
    """Returns all incomes, savings, and expenses for the initial page load."""
    year = user.year
    provider = DetailedDataProvider(user)

    expense_contexts = [
        DetailedContextPresenter.build(
            title=f"{_('Expenses')} / {expense_type_title}",
            url_title=slugify(expense_type_title),
            dto=dto,
            year=year,
            order=""
        )
        for expense_type_title, dto in provider.get_expenses().items()
    ]

    return {
        "income": DetailedContextPresenter.build(
            title=_("Incomes"), url_title="income", dto=provider.get_incomes(), year=year, order=""
        ),
        "saving": DetailedContextPresenter.build(
            title=_("Savings"), url_title="saving", dto=provider.get_savings(), year=year, order=""
        ),
        "expense": expense_contexts,
    }


def load_partial_service(user: User, category: str, order: str) -> dict:
    """Returns ONLY the specific category requested for dynamic HTMX sorting."""
    year = user.year
    provider = DetailedDataProvider(user)

    if category == "incomes":
        title = _("Incomes")
        dto = provider.get_incomes()
    elif category == "savings":
        title = _("Savings")
        dto = provider.get_savings()
    else:
        title = f"{_('Expenses')} / {category.replace('-', ' ').title()}"
        dto = provider.get_expense(category_slug=category)

    return DetailedContextPresenter.build(
        title=title,
        url_title=category,
        dto=dto,
        year=year,
        order=order
    )