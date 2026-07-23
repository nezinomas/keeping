from ....core.lib.date import years
from ...lib.drinks_options import DrinkConverter
from ...lib.drinks_stats import DrinkStats
from ..calendar_chart import CalendarChart
from .builders import IndexBuilder, LimitCardViewModel
from .providers import IndexDataProvider


def load_service(user, year: int) -> dict:
    data = IndexDataProvider(user, year).get_data()
    converter = DrinkConverter(user.drink_type)
    stats = DrinkStats(converter, data.sum_by_month)

    builder = IndexBuilder(
        converter=converter,
        drink_stats=stats,
        target=data.target,
        latest_past_date=data.latest_past_date,
        latest_current_date=data.latest_current_date,
    )

    calendar_service = CalendarChart(
        year=year,
        drink_type=user.drink_type,
        daily_data=data.sum_by_day,
        latest_past_date=data.latest_past_date,
    )

    limit = LimitCardViewModel(
        has_data=data.target_id > 0,
        ml=data.target,
        pcs=data.target_pcs,
        target_id=data.target_id,
    )

    return {
        "all_years": len(years()),
        "chart_quantity": builder.chart_quantity(),
        "chart_consumption": builder.chart_consumption(),
        "tbl_std_av": builder.tbl_std_av(),
        "cards": builder.get_cards(),
        "limit": limit,
        "calendar": calendar_service.year_grid(),
    }
