from django.utils.translation import gettext as _

from ...pensions.services.model_services import PensionBalanceModelService
from ...savings.models import SavingType
from ...savings.services.model_services import SavingBalanceModelService
from .savings import table_total_row

PENSION_TYPES = [SavingType.Types.PENSIONS]


def load_service(user, year: int) -> dict:
    """The Pensions table: its Funds of kind Pensijos, then its Pension funds."""
    savings_as_pensions = list(
        SavingBalanceModelService(user).year_of_types(year, PENSION_TYPES)
    )
    rows = savings_as_pensions + list(PensionBalanceModelService(user).year(year))
    return {
        "title": _("Pensions"),
        "object_list": rows,
        "total_row": table_total_row(
            user, year, PENSION_TYPES, rows, saving_rows=savings_as_pensions
        ),
    }
