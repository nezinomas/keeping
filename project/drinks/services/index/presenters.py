from ....core.lib.date import years
from ...lib.drinks_options import DrinkConverter
from ...lib.drinks_stats import DrinkStats
from ..calendar_chart import CalendarChart
from .builders import IndexBuilder
from .providers import IndexDataProvider


def load_service(user, year: int) -> dict:
    data = IndexDataProvider(user, year).get_data()
    options = DrinkConverter(user.drink_type)
    stats = DrinkStats(options, data.sum_by_month)

    builder = IndexBuilder(
        options=options,
        drink_stats=stats,
        target=data.target,
        latest_past_date=data.latest_past_date,
        latest_current_date=data.latest_current_date,
    )

    calendar_service = CalendarChart(
        year=year,
        drink_type=user.drink_type,
        data=data.sum_by_day,
        latest_past_date=data.latest_past_date,
    )

    return {
        "all_years": len(years()),
        "chart_quantity": builder.chart_quantity(),
        "chart_consumption": builder.chart_consumption(),
        "chart_calendar_1H": calendar_service.first_half_of_year(),
        "chart_calendar_2H": calendar_service.second_half_of_year(),
        "tbl_consumption": builder.tbl_consumption(),
        "tbl_dray_days": builder.tbl_dry_days(),
        "tbl_alcohol": builder.tbl_alcohol(),
        "tbl_std_av": builder.tbl_std_av(),
    }
