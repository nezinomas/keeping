from dataclasses import dataclass

from django.urls import reverse
from django.utils.translation import gettext as _

from ...core.lib import stat_card
from ...core.lib.stat_card import StatCard
from ...users.models import User
from ..models import BookTarget
from .model_services import BookModelService, BookTargetModelService


@dataclass
class Cards:
    """The three figures a Reading year reports, as Cards.

    Finished, Reading, Goal — the year's count is the headline. All three are
    stated as recorded: no tone, no arrow, no comparison against last year, and
    no note, because a note explains a figure against something else and these
    stand on their own. Only the Goal has an empty form: a goal can be absent,
    where a count of zero is still a count. See CONTEXT.md, "Card".
    """

    user: User
    year: int

    @classmethod
    def build(cls, user: User, year: int) -> list[StatCard]:
        return cls(user, year)._cards()

    def _cards(self) -> list[StatCard]:
        return [self._finished(), self._reading(), self._goal()]

    def _finished(self) -> StatCard:
        qs = BookModelService(self.user).finished().filter(year=self.year)
        count = qs[0]["cnt"] if qs.exists() else 0

        return StatCard(title=_("Finished"), value=str(count))

    def _reading(self) -> StatCard:
        qs = BookModelService(self.user).reading(self.year)
        count = qs["reading"] if qs else 0

        return StatCard(title=_("Reading"), value=str(count))

    def _goal(self) -> StatCard:
        title = _("Goal")

        try:
            target = BookTargetModelService(self.user).objects.get(year=self.year)
        except BookTarget.DoesNotExist:
            return StatCard(
                title=title,
                note=_("No goal set"),
                state=stat_card.EMPTY,
                edit_url=reverse("books:target_new"),
                edit_label=_("New goal"),
            )

        return StatCard(
            title=title,
            value=str(target.quantity),
            edit_url=reverse("books:target_update", kwargs={"pk": target.pk}),
            edit_label=_("Update goal"),
        )
