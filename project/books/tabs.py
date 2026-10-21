from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from ..core.tabs import Tab, Tabs

YEAR = "year"
ALL_RECORDS = "all"


class BookTab(Tab):
    app = "books"


class BookDataTab(BookTab):
    @property
    def url(self) -> str:
        return reverse("books:tab_data", kwargs={"scope": YEAR})


TABS = Tabs(BookTab("index", _("Overview")), BookDataTab("data", _("Data")))
