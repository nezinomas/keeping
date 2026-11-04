from django.utils.translation import gettext_lazy as _

from ..core.tabs import Tab, Tabs


class TransactionTab(Tab):
    app = "transactions"


TABS = Tabs(
    TransactionTab("transactions", _("Transactions")),
    TransactionTab("sales", _("Fund sales")),
    TransactionTab("switches", _("Fund switches")),
    TransactionTab("accounts", _("Accounts")),
)
