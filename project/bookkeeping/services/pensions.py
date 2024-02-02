import itertools as it

from django.utils.translation import gettext as _

from ...core.lib import utils
from ...pensions.models import PensionBalance
from ...savings.models import SavingBalance


def get_data(year) -> list:
    pensions = PensionBalance.objects.year(year)
    savings_as_pensions = SavingBalance.objects.year(year).filter(saving_type__type="pensions")
    return list(it.chain(savings_as_pensions, pensions))


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
    ]

    return {
        "title": _("Pensions"),
        "type": "pensions",
        "object_list": data,
        "total_row": utils.total_row(data, fields),
    }