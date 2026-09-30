from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext as _

from ....core.lib.table_order import Column, TableOrder
from ....users.models import User
from .builders import DetailedTableBuilder
from .dtos import DetailedDto
from .providers import DetailedDataProvider

MONTHS = tuple(str(month) for month in range(1, 13))

ORDER = TableOrder(
    columns=(
        Column("title"),
        *(Column(month, descending=True) for month in MONTHS),
        Column("total_col", descending=True),
    ),
    default="title",
)


def build_context(
    title: str, url_title: str, dto: DetailedDto, year: int, order: str, url: str = ""
) -> dict:
    if not dto.data:
        return {}

    builder = DetailedTableBuilder(dto, year)
    ordered = ORDER.sort(order, builder.table, values=lambda row: row)

    return {
        "title": title,
        "url_title": url_title,
        "url": url,
        "table_id": f"detailed-{url_title}-table",
        "data": ordered.rows,
        "total": builder.total_row,
        "order": ordered.active,
    }


def _incomes(provider: DetailedDataProvider) -> tuple:
    return (_("Incomes"), "income", "", provider.get_incomes())


def _savings(provider: DetailedDataProvider) -> tuple:
    return (_("Savings"), "saving", "", provider.get_savings())


def _expense_type(title: str, type_slug: str, dto: DetailedDto) -> tuple:
    url = reverse("bookkeeping:detailed_type", kwargs={"type_slug": type_slug})
    return (title, type_slug, url, dto)


def _expense_types(type_slug: str, provider: DetailedDataProvider) -> list[tuple]:
    if not type_slug:
        return [
            _expense_type(title, slugify(title), dto)
            for title, dto in provider.get_expenses().items()
            if dto.data
        ]

    expense_type = provider.get_expense_type(type_slug)
    if not expense_type:
        return []

    dto = provider.get_expense(expense_type.slug)
    return [_expense_type(expense_type.title, expense_type.slug, dto)]


def _get_categories(
    category: str, type_slug: str, provider: DetailedDataProvider
) -> list[tuple[str, str, str, DetailedDto]]:
    match category:
        case "income":
            return [_incomes(provider)]

        case "saving":
            return [_savings(provider)]

        case "expenses":
            return _expense_types(type_slug, provider)

        case _:
            return []


def load_service(
    user: User, category: str, order: str = "", type_slug: str = ""
) -> list[dict]:
    provider = DetailedDataProvider(user)
    contexts = []

    categories = _get_categories(category, type_slug, provider)

    for title, url_title, url, dto in categories:
        if context := build_context(
            title=title,
            url_title=url_title,
            dto=dto,
            year=user.year,
            order=order,
            url=url,
        ):
            contexts.append(context)

    return sorted(contexts, key=lambda table: table["total"]["total_col"], reverse=True)
