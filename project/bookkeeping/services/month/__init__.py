import itertools as it

from ....core.lib.date import current_day
from ....users.models import User
from .presenters import MonthContextPresenter
from .providers import MonthDataProvider


def load_service(user: User) -> dict:
    year = user.year
    month = user.month

    dto = MonthDataProvider(user).get_data()

    presenter = MonthContextPresenter(year, month, dto)

    return {
        "month_table": {
            "day": current_day(year, month, False),
            "expenses": it.zip_longest(
                presenter.tables["main_table"], presenter.tables["spending_table"]
            ),
            "expense_types": dto.expense_types,
            "total_row": presenter.tables["total_row"],
        },
        "info": presenter.info_context,
        "chart_expenses": presenter.charts.build_expenses(),
        "chart_targets": presenter.charts.build_targets(),
    }