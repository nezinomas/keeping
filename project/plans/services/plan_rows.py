from dataclasses import dataclass

from django.urls import reverse

from ..lib.month_states import WITHIN

MONTHS = range(1, 13)


@dataclass(frozen=True)
class PlanRow:
    title: str
    update_url: str
    delete_url: str
    cells: list[tuple[int, str]]


@dataclass(frozen=True)
class PlanUrls:
    update: str
    delete: str

    def row(
        self, title, months: dict[int, int], *url_args, states=(WITHIN,) * len(MONTHS)
    ):
        return PlanRow(
            title=str(title),
            update_url=reverse(self.update, args=url_args),
            delete_url=reverse(self.delete, args=url_args),
            cells=[
                (months.get(month, 0), state) for month, state in zip(MONTHS, states)
            ],
        )
