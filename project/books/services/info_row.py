from dataclasses import dataclass, field

from ...users.models import User
from ..models import BookTarget
from .model_services import BookModelService, BookTargetModelService


@dataclass
class InfoRow:
    user: User
    readed: int = 0
    reading: int = 0
    target: BookTarget = 0
    year: int = field(init=False, default=None)

    def __post_init__(self):
        self.year = self.user.year
        self.readed = self._readed()
        self.reading = self._reading()
        self.target = self._target()

    def _readed(self):
        qs = BookModelService(self.user).readed().filter(year=self.year)

        return qs[0]["cnt"] if qs.exists() else 0

    def _reading(self):
        return (
            qs["reading"]
            if (qs := BookModelService(self.user).reading(self.year))
            else 0
        )

    def _target(self):
        try:
            qs = BookTargetModelService(self.user).objects.get(year=self.year)
        except BookTarget.DoesNotExist:
            return 0

        return qs
