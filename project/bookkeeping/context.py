from ..savings.tabs import TABS as SAVING_TABS
from ..transactions.tabs import TABS as TRANSACTION_TABS


def nav_tab_menus(request):
    return {
        "nav_tab_menus": {
            "transactions": TRANSACTION_TABS,
            "savings": SAVING_TABS,
        }
    }
