from ....users.models import User
from .presenters import build_context
from .providers import WealthDataProvider


def load_service(user: User, year: int) -> dict:
    provider = WealthDataProvider(user, year)
    dto = provider.get_wealth_data()
    return build_context(dto)
