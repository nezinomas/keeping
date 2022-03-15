from ...core.lib import utils


class DrinksOptions():
    ratios = {
        'beer': {'stdav': 2.5, 'ml': 500},  # 500ml -> 2.5 std_av
        'wine': {'stdav': 8, 'ml': 750},  # 750ml -> 8 std_av
        'vodka': {'stdav': 40, 'ml': 1000},  # 1000ml -> 40 std_av
    }

    def __init__(self, drink_type: str = None):
        if not drink_type:
            drink_type = utils.get_user().drink_type

        self.drink_type = drink_type

    @property
    def ratio(self) -> float:
        return 1 / self.ratios.get(self.drink_type, {}).get('stdav', 1)

    @property
    def stdav(self) -> float:
        return self.ratios.get(self.drink_type, {}).get('stdav', 1)

    def convert(self, qty: float, to: str) -> float:
        stdav = qty * self.stdav

        return stdav / self.ratios.get(to, {}).get('stdav', 1)

    def ml_to_stdav(self, drink_type: str, ml: int):
        _node = self.ratios.get(drink_type, {})
        _ml = _node.get('ml', 1)
        _stdav = _node.get('stdav', 1)

        _converted = (ml * _stdav) / _ml

        return _converted

    def stdav_to_ml(self, drink_type: str, stdav: float):
        _node = self.ratios.get(drink_type, {})
        _ml = _node.get('ml', 1)
        _stdav = _node.get('stdav', 1)

        _converted = (stdav * _ml) / _stdav

        return _converted

    def stdav_to_alkohol(self, stdav: float, drink_type: str = None):
        if not drink_type:
            drink_type = self.drink_type

        _node = self.ratios.get(drink_type, {})
        _stdav = _node.get('stdav', 1)

        # one stdav = 10g pure alkohol (100%)
        return _stdav * 0.01
