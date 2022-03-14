from ...core.lib import utils


class DrinksOptions():
    ratios = {
        'beer': 2.5,  # 500ml -> 2.5 std_av
        'wine': 8,  # 750ml -> 8 std_av
        'vodka': 40,  # 1000ml -> 40 std_av
    }

    def __init__(self, drink_type: str = None):
        if not drink_type:
            drink_type = utils.get_user().drink_type

        self._drink_type = drink_type

    @property
    def ratio(self) -> float:
        return 1 / self.ratios.get(self._drink_type, 1)

    @property
    def stdav(self) -> float:
        return self.ratios.get(self._drink_type, 1)

    def get_ratio(self, drink_type: str) -> float:
        return 1 / self.ratios.get(drink_type, 1)

    def convert(self, qty: float, to: str) -> float:
        stdav = qty * self.stdav

        return stdav / self.ratios.get(to, 1)
