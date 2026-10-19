from django.utils.translation import gettext_lazy as _

from ..core.tabs import Tab, Tabs


class BookTab(Tab):
    app = "books"


TABS = Tabs(BookTab("index", _("Overview")), BookTab("data", _("Data")))
