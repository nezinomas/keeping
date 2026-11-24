from datetime import date

from ....users.models import User
from ..index.presenters import year_strip_titles
from .calculators import ForecastCalculator
from .providers import ForecastDataProvider


def get_month(year: int, today: date) -> int:
    if year > today.year:
        return 1

    return 12 if year < today.year else today.month


def load_service(user: User, today: date) -> dict:
    year = user.selected_year()
    month = get_month(year, today)

    provider = ForecastDataProvider(user)
    forecast_data = provider.get_forecast_data()

    forecast_value = ForecastCalculator(month, forecast_data).forecast()

    beginning = provider.get_beginning_balance()
    end = beginning + forecast_value

    return {
        "title": year_strip_titles(year),
        "data": [beginning, end, forecast_value],
        "highlight": [False, False, True],
    }
