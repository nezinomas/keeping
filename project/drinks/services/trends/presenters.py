from ...lib.drinks_options import DrinkConverter
from ...lib.drinks_trend import TrendStats
from .builders import TrendsBuilder
from .providers import TrendsDataProvider


def load_service(user, year: int) -> dict:
    data = TrendsDataProvider(user, year).get_data()
    converter = DrinkConverter(user.drink_type)
    stats = TrendStats(
        converter,
        current_daily=data.current_daily,
        past_daily=data.past_daily,
        target=data.target,
    )

    builder = TrendsBuilder(drink_stats=stats, target=data.target)

    return {
        "chart_trend": builder.chart_trend(),
        "trend_slope": builder.trend_slope(),
        "trend_ytd": builder.trend_ytd(),
        "trend_projection": builder.trend_projection(),
    }
