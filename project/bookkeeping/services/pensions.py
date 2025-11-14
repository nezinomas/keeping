import itertools as it

from django.utils.translation import gettext as _

from ...core.lib import utils
from ...pensions.services.model_services import PensionBalanceModelService
from ...savings.services.model_services import SavingBalanceModelService


def get_data(user, year) -> list:
    pensions = PensionBalanceModelService(user).year(year)
    savings_as_pensions = SavingBalanceModelService(user).year(year).filter(
        saving_type__type="pensions"
    )
    return list(it.chain(savings_as_pensions, pensions))


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
        "title": _("Pensions"),
        "type": "pensions",
        "object_list": data,
        "total_row": utils.total_row(data, fields),
    }
