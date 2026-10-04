from django.utils.translation import gettext as _

from ...core.lib import utils
from ...pensions.services.model_services import PensionBalanceModelService
from ...savings.models import SavingType
from ...savings.services.model_services import SavingBalanceModelService
from ...transactions.services.model_services import SavingChangeModelService
from .savings import hidden_funds

PENSION_TYPES = [SavingType.Types.PENSIONS]


def get_data(user, year) -> tuple[list, list]:
    """The savings-as-pensions rows and the pension rows."""
    savings_as_pensions = list(
        SavingBalanceModelService(user).year(year, types=PENSION_TYPES)
    )
    return savings_as_pensions, list(PensionBalanceModelService(user).year(year))


def load_service(user, year: int) -> dict:
    savings_as_pensions, pensions = get_data(user, year)
    data = savings_as_pensions + pensions
    switched_within = SavingChangeModelService(user).switched_within(
        year, PENSION_TYPES, hidden=hidden_funds(savings_as_pensions)
    )
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
        "total_row": utils.funds_total_row(data, fields, switched_within),
    }
