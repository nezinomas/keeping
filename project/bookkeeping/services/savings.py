from django.db.models import Sum
from django.utils.translation import gettext as _

from ...core.lib.money_cells import euros, percent
from ...core.lib.stat_card import Card, EmptyStatCard, StatCard
from ...incomes.services.model_services import IncomeModelService
from ...savings.models import SavingType
from ...savings.services.model_services import (
    SavingBalanceModelService,
    SavingModelService,
)
from ...transactions.services.model_services import SavingChangeModelService
from ..lib.total_rows import funds_total_row

FUND_TYPES = [t for t in SavingType.Types.values if t != SavingType.Types.PENSIONS]
FUNDS_TABLE_FIELDS = [
    "past_amount",
    "past_fee",
    "per_year_incomes",
    "per_year_fee",
    "fee",
    "incomes",
    "sold",
    "sold_fee",
    "market_value",
    "profit_sum",
    "profit_proc",
]


def hidden_funds(rows) -> frozenset[int]:
    """Ids of the funds whose row shows no profit."""
    return frozenset(row.saving_type_id for row in rows if not row.shows_profit)


def table_total_row(user, year: int, types, rows, saving_rows) -> dict:
    """A funds table's Total row, its percent on a base that counts money switched
    between the table's funds of `types` once.

    `saving_rows` are the table's SavingBalance rows: a switch through one that shows
    no profit still counts (`hidden_funds`)."""
    switched_within = SavingChangeModelService(user).switched_within(
        year, types, hidden=hidden_funds(saving_rows)
    )
    return funds_total_row(rows, FUNDS_TABLE_FIELDS, switched_within)


def saved_share(savings_total: int, incomes_total: int) -> Card:
    """What the year's savings took of its incomes, the savings' sum as the note;
    empty with no incomes, and with no note when there are no savings either."""
    title = _("Percentage of income saved")
    if not incomes_total and not savings_total:
        return EmptyStatCard(title)

    note = f"{euros(savings_total, '2g')} €"
    if not incomes_total:
        return EmptyStatCard(title, note=note)

    return StatCard(
        title,
        value=percent(savings_total / incomes_total * 100),
        unit="%",
        note=note,
    )


def _year_sum(service, year: int) -> int:
    return service.year(year).aggregate(Sum("price", default=0))["price__sum"]


def load_service(user, year: int) -> dict:
    savings = list(SavingBalanceModelService(user).year_of_types(year, FUND_TYPES))
    share = saved_share(
        _year_sum(SavingModelService(user), year),
        _year_sum(IncomeModelService(user), year),
    )
    return {
        "title": _("Funds"),
        "object_list": savings,
        "saved_share": share,
        "total_row": table_total_row(
            user, year, FUND_TYPES, savings, saving_rows=savings
        ),
    }
