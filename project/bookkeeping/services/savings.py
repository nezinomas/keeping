from dataclasses import dataclass

from django.db.models import Sum
from django.utils.translation import gettext as _

from ...core.lib import utils
from ...incomes.models import Income
from ...savings.models import Saving, SavingBalance


@dataclass
class Data:
    savings: list
    savings_total: int
    incomes_total: int


def get_data(year: int) -> Data:
    incomes_total = (
        Income.objects.related()
        .year(year=year)
        .aggregate(Sum("price", default=0))["price__sum"]
    )

    savings_total = (
        Saving.objects.related()
        .year(year)
        .aggregate(Sum("price", default=0))["price__sum"]
    )

    savings = SavingBalance.objects.year(year).exclude(
        saving_type__type="pensions"
    )
    return Data(savings, savings_total, incomes_total)


def load_service(year: int) -> dict:
    data = get_data(year)
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
