from django.utils.translation import gettext as _

from .dtos import WealthDto


class WealthPresenter:
    def __init__(self, dto: WealthDto):
        self.dto = dto

    @property
    def money(self) -> float:
        return self.dto.account_balance + self.dto.saving_balance

    @property
    def wealth(self) -> float:
        return (
            self.dto.account_balance
            + self.dto.saving_balance
            + self.dto.pension_balance
        )


def build_context(dto: WealthDto) -> dict:
    presenter = WealthPresenter(dto)
    return {
        "data": {
            "title": [_("Money"), _("Wealth")],
            "data": [presenter.money, presenter.wealth],
        }
    }


def load_service(user, year: int) -> dict:
    from .providers import WealthDataProvider

    provider = WealthDataProvider(user, year)
    dto = provider.get_wealth_data()
    return build_context(dto)
