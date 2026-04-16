from datetime import datetime
from typing import cast

from ....users.models import User
from .calculators import ForecastCalculator
from .providers import ForecastDataProvider


def get_month(year: int) -> int:
    now = datetime.now()

    if year > now.year:
        return 1

    return 12 if year < now.year else now.month


def load_service(user: User) -> dict:
    year = cast(int, user.year)
    month = get_month(year)

    provider = ForecastDataProvider(user)
    forecast_data = provider.get_forecast_data()

    forecast_value = ForecastCalculator(month, forecast_data).forecast()

    beginning = provider.get_beginning_balance()
    end = beginning + forecast_value

    return {
        "data": [beginning, end, forecast_value],
        "highlight": [False, False, True],
    }
