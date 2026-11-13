from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _

from ..core.tabs import Tab, Tabs
from .models import Debt


@dataclass(frozen=True)
class DebtTab(Tab):
    app = "debts"
    debt_type: Debt.DebtType
    template: str

    @property
    def template_name(self) -> str:
        return f"debts/tab_{self.template}.html"


TABS = Tabs(
    DebtTab("lend", _("Lend"), Debt.DebtType.LEND, "debts"),
    DebtTab("lend_returns", _("Lend return"), Debt.DebtType.LEND, "returns"),
    DebtTab("borrow", _("Borrow"), Debt.DebtType.BORROW, "debts"),
    DebtTab("borrow_returns", _("Borrow return"), Debt.DebtType.BORROW, "returns"),
)

DEBT_TABS = {
    Debt.DebtType.LEND: TABS["lend"],
    Debt.DebtType.BORROW: TABS["borrow"],
}

RETURN_TABS = {
    Debt.DebtType.LEND: TABS["lend_returns"],
    Debt.DebtType.BORROW: TABS["borrow_returns"],
}
