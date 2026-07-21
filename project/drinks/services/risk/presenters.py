from ...lib.drinks_risk import RiskStats
from ...lib.drinks_stats import DataRow
from .builders import RiskBuilder
from .providers import RiskDataProvider


def load_service(user, year: int) -> dict:
    data = RiskDataProvider(user, year).get_data()

    current_daily = (
        [DataRow(**row) for row in data.current_daily] if data.current_daily else []
    )
    past_daily = [DataRow(**row) for row in data.past_daily] if data.past_daily else []

    stats = RiskStats(current_daily=current_daily, past_daily=past_daily)
    builder = RiskBuilder(drink_stats=stats)

    return {
        "cards": builder.get_cards(),
        "chart_weekly": builder.chart_weekly(),
        "chart_heavy": builder.chart_heavy_days(),
    }
