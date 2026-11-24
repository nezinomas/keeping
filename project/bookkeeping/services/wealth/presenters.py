from ....users.models import User
from .dtos import WealthDto
from .providers import WealthDataProvider


class WealthPresenter:
    def __init__(self, dto: WealthDto):
        self.dto = dto

    @property
    def money(self) -> int:
        return self.dto.account_balance + self.dto.saving_balance

    @property
    def wealth(self) -> int:
        return (
            self.dto.account_balance
            + self.dto.saving_balance
            + self.dto.pension_balance
        )


def load_service(user: User, year: int, account_balance: int) -> WealthPresenter:
    return WealthPresenter(
        WealthDataProvider(user, year).get_wealth_data(account_balance)
    )
