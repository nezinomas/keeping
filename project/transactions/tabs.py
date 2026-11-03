from django.utils.translation import gettext_lazy as _

from ..core.tabs import Tab, Tabs


class TransactionTab(Tab):
    app = "transactions"


TABS = Tabs(TransactionTab("transactions", _("Transactions")))
