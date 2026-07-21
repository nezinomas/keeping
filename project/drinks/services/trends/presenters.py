from ...lib.drinks_options import DrinkConverter
from ...lib.drinks_stats import DataRow
from ...lib.drinks_trend import TrendStats
from .builders import TrendsBuilder
from .providers import TrendsDataProvider


def load_service(user, year: int) -> dict:
    data = TrendsDataProvider(user, year).get_data()
    converter = DrinkConverter(user.drink_type)

    current_daily = (
        [DataRow(**row) for row in data.current_daily] if data.current_daily else []
    )
    past_daily = [DataRow(**row) for row in data.past_daily] if data.past_daily else []

    stats = TrendStats(
        converter,
        current_daily=current_daily,
        past_daily=past_daily,
        target=data.target,
    )

    builder = TrendsBuilder(drink_stats=stats, target=data.target)

    return {
        "chart_trend": builder.chart_trend(),
        "trend_items": builder.trend_items(),
        "trend_ytd": builder.trend_ytd(),
        "trend_projection": builder.trend_projection(),
    }
