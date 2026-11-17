from django.utils.translation import gettext as _

from ...core.lib import utils
from ...pensions.services.model_services import PensionBalanceModelService
from ...savings.models import SavingType
from ...savings.services.model_services import SavingBalanceModelService
from ...transactions.services.model_services import SavingChangeModelService
from .savings import FUNDS_TABLE_FIELDS, hidden_funds

PENSION_TYPES = [SavingType.Types.PENSIONS]


def get_data(user, year) -> tuple[list, list]:
    """The savings-as-pensions rows and the pension rows."""
    savings_as_pensions = list(
        SavingBalanceModelService(user).year_of_types(year, PENSION_TYPES)
    )
    return savings_as_pensions, list(PensionBalanceModelService(user).year(year))


def load_service(user, year: int) -> dict:
    savings_as_pensions, pensions = get_data(user, year)
    data = savings_as_pensions + pensions
    switched_within = SavingChangeModelService(user).switched_within(
        year, PENSION_TYPES, hidden=hidden_funds(savings_as_pensions)
    )

    return {
        "title": _("Pensions"),
        "type": "pensions",
        "object_list": data,
        "total_row": utils.funds_total_row(data, FUNDS_TABLE_FIELDS, switched_within),
    }
