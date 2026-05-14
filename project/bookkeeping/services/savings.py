from dataclasses import dataclass
from typing import Any

from django.db.models import Sum
from django.utils.translation import gettext as _

from ...core.lib import utils
from ...incomes.services.model_services import IncomeModelService
from ...savings.services.model_services import (
    SavingBalanceModelService,
    SavingModelService,
)


@dataclass
class SavingsDto:
    savings: list[Any]
    savings_total: float
    incomes_total: float


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
            SavingBalanceModelService(self._user)
            .year(self._year)
            .exclude(saving_type__type="pensions")
        )
        return SavingsDto(
            savings=savings,
            savings_total=savings_total,
            incomes_total=incomes_total,
        )


class SavingsPresenter:
    _FIELDS = [
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

    def __init__(self, dto: SavingsDto):
        self._dto = dto

    def as_dict(self) -> dict:
        return {
            "title": _("Funds"),
            "type": "savings",
            "object_list": self._dto.savings,
            "incomes_total": self._dto.incomes_total,
            "savings_total": self._dto.savings_total,
            "total_row": utils.total_row(self._dto.savings, self._FIELDS),
        }


def get_data(user, year: int) -> SavingsDto:
    return SavingsService(user, year).get_data()


def load_service(user, year: int) -> dict:
    dto = get_data(user, year)
    return SavingsPresenter(dto).as_dict()
