from datetime import date

from django.db import models

from ..core.models import TitleAbstract
from ..core.validators import title_characters_in


class Journal(TitleAbstract):
    first_record = models.DateField(default=date.today, editable=False)
    unnecessary_expenses = models.CharField(max_length=254, null=True, blank=True)
    unnecessary_savings = models.BooleanField(default=False)
    lang = models.CharField(max_length=2, blank=False, default="en")

    def __str__(self):
        return f"{self.title}"

    @classmethod
    def title_for(cls, username: str) -> str:
        kept = title_characters_in(username)
        suffix = " Journal"
        room = cls._meta.get_field("title").max_length - len(suffix)

        title = "Journal"
        if kept:
            title = f"{kept[:room]}{suffix}"
        return title
