from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from ..core.tabs import Tab, Tabs


class CountTab(Tab):
    app = "counts"

    @property
    def url_name(self) -> str:
        return f"counts:tab_{self.name}"

    # every counts route belongs to one Counter, so a url needs the slug too
    def url(self, slug: str) -> str:
        return reverse(self.url_name, kwargs={"slug": slug})

    @property
    def reload_trigger(self) -> str:
        return f"reload{self.name.title()}"


TABS = Tabs(
    CountTab("index", _("Overview")),
    CountTab("periodicity", _("Periodicity")),
    CountTab("history", _("History")),
    CountTab("data", _("Data")),
)
