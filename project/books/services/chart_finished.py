import operator
from dataclasses import dataclass, field

from django.utils.translation import gettext as _

from ...users.models import User
from .model_services import BookModelService, BookTargetModelService


@dataclass
class ChartFinishedData:
    user: User
    targets: dict = field(init=False, default_factory=dict)
    finished: dict = field(init=False, default_factory=dict)

    def __post_init__(self):
        self.targets = dict(
            BookTargetModelService(self.user).objects.values_list("year", "quantity")
        )
        self.finished = dict(
            BookModelService(self.user).finished().values_list("year", "cnt")
        )


class ChartFinished:
    def __init__(self, data: ChartFinishedData):
        self._finished = data.finished
        self._targets = data.targets

    def context(self):
        data = self._make_serries_data()

        return {
            "categories": list(self._finished.keys()),
            "data": data,
            "targets": list(map(operator.itemgetter("target"), data)),
            "chart_title": _("Finished books"),
        }

    def _make_serries_data(self):
        return [
            {
                "y": cnt,
                "target": self._targets.get(year, 0),
            }
            for year, cnt in self._finished.items()
        ]
