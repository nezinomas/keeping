from dataclasses import dataclass
from typing import ClassVar

from django.urls import reverse


@dataclass(frozen=True)
class Tab:
    app: ClassVar[str]
    name: str
    title: str

    @property
    def url(self) -> str:
        return reverse(f"{self.app}:tab_{self.name}")

    @property
    def template_name(self) -> str:
        return f"{self.app}/tab_{self.name}.html"


class Tabs(tuple):
    def __new__(cls, *tabs: Tab):
        return super().__new__(cls, tabs)

    def __getitem__(self, key):
        if not isinstance(key, str):
            return super().__getitem__(key)

        for tab in self:
            if tab.name == key:
                return tab
        raise KeyError(key)
