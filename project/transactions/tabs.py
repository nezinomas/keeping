from django.utils.translation import gettext_lazy as _

from ..core.tabs import Tab, Tabs
from .services.account_scope import OPEN, AccountScope


class TransactionTab(Tab):
    app = "transactions"


class AccountsTab(TransactionTab):
    @property
    def url(self) -> str:
        return AccountScope(OPEN).url()


TABS = Tabs(
    TransactionTab("transactions", _("Transactions")),
    TransactionTab("sales", _("Fund sales")),
    TransactionTab("switches", _("Fund switches")),
    AccountsTab("accounts", _("Accounts")),
)
