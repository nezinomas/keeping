from dataclasses import dataclass
from typing import Any

from django.db.models import Sum
from django.utils.translation import gettext as _

from ...core.lib import utils
from ...core.lib.money_cells import percent
from ...core.lib.stat_card import Card, EmptyStatCard, StatCard
from ...incomes.services.model_services import IncomeModelService
from ...savings.models import SavingType
from ...savings.services.model_services import (
    SavingBalanceModelService,
    SavingModelService,
)
from ...transactions.services.model_services import SavingChangeModelService

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


@dataclass
class SavingsDto:
    savings: list[Any]
    savings_total: int
    incomes_total: int
    switched_within: int


class SavingsService:
    def __init__(self, user, year: int):
        self._user = user
        self._year = year

    def get_data(self) -> SavingsDto:
        incomes_total = (
            IncomeModelService(self._user)
            .year(self._year)
            .aggregate(Sum("price", default=0))["price__sum"]
        )
        savings_total = (
            SavingModelService(self._user)
            .year(self._year)
            .aggregate(Sum("price", default=0))["price__sum"]
        )
        savings = list(
            SavingBalanceModelService(self._user).year_of_types(self._year, FUND_TYPES)
        )
        switched_within = SavingChangeModelService(self._user).switched_within(
            self._year, FUND_TYPES, hidden=hidden_funds(savings)
        )
        return SavingsDto(
            savings=savings,
            savings_total=savings_total,
            incomes_total=incomes_total,
            switched_within=switched_within,
        )


class SavingsPresenter:
    def __init__(self, dto: SavingsDto):
        self._dto = dto

    def saved_share(self) -> Card:
        """What the year's savings took of its incomes; empty with no incomes."""
        title = _("Percentage of income saved")
        if not self._dto.incomes_total:
            return EmptyStatCard(title)

        share = self._dto.savings_total / self._dto.incomes_total * 100
        return StatCard(title, value=percent(share), unit="%")

    def as_dict(self) -> dict:
        return {
            "title": _("Funds"),
            "type": "savings",
            "object_list": self._dto.savings,
            "saved_share": self.saved_share(),
            "total_row": utils.funds_total_row(
                self._dto.savings, FUNDS_TABLE_FIELDS, self._dto.switched_within
            ),
        }


def get_data(user, year: int) -> SavingsDto:
    return SavingsService(user, year).get_data()


def load_service(user, year: int) -> dict:
    dto = get_data(user, year)
    return SavingsPresenter(dto).as_dict()
