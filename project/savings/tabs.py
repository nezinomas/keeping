from django.utils.translation import gettext_lazy as _

from ..core.tabs import Tab, Tabs


class SavingTab(Tab):
    app = "savings"


TABS = Tabs(SavingTab("savings", _("Savings")))
