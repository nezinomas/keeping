from dataclasses import dataclass

from django.db.models import Sum
from django.utils.translation import gettext as _

from ...core.lib import utils
from ...incomes.services.model_services import IncomeModelService
from ...savings.services.model_services import (
    SavingBalanceModelService,
    SavingModelService,
)


@dataclass
class Data:
    savings: list
    savings_total: int
    incomes_total: int


def get_data(user, year: int) -> Data:
    incomes_total = (
        IncomeModelService(user)
        .year(year)
        .aggregate(Sum("price", default=0))["price__sum"]
    )
    savings_total = (
        SavingModelService(user)
        .year(year)
        .aggregate(Sum("price", default=0))["price__sum"]
    )
    savings = (
        SavingBalanceModelService(user).year(year).exclude(saving_type__type="pensions")
    )
    return Data(savings, savings_total, incomes_total)


def load_service(user, year: int) -> dict:
    data = get_data(user, year)
    fields = [
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

    return {
        "title": _("Funds"),
        "type": "savings",
        "object_list": data.savings,
        "incomes_total": data.incomes_total,
        "savings_total": data.savings_total,
        "total_row": utils.total_row(data.savings, fields),
    }
