import operator
from dataclasses import dataclass, field

from django.utils.translation import gettext as _

from .model_services import BookModelService, BookTargetModelService
from ...users.models import User


@dataclass
class ChartReadedData:
    user: User
    targets: dict = field(init=False, default_factory=dict)
    readed: dict = field(init=False, default_factory=dict)

    def __post_init__(self):
        self.targets = dict(BookTargetModelService(self.user).objects.values_list("year", "quantity"))
        self.readed = dict(BookModelService(self.user).readed().values_list("year", "cnt"))


class ChartReaded:
    def __init__(self, data: ChartReadedData):
        self._readed = data.readed
        self._targets = data.targets

    def context(self):
        data = self._make_serries_data()

        return {
            "categories": list(self._readed.keys()),
            "data": data,
            "targets": list(map(operator.itemgetter("target"), data)),
            "chart_title": _("Readed books"),
            "chart_column_color": "70, 171, 157",
        }

    def _make_serries_data(self):
        return [
            {
                "y": cnt,
                "target": self._targets.get(year, 0),
            }
            for year, cnt in self._readed.items()
        ]
