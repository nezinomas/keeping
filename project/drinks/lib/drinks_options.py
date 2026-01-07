from ...core.lib.date import ydays


class DrinksOptions:
    ratios = {
        "beer": {"stdav": 2.5, "ml": 500},  # 500ml -> 2.5 std_av
        "wine": {"stdav": 8, "ml": 750},  # 750ml -> 8 std_av
        "vodka": {"stdav": 40, "ml": 1000},  # 1000ml -> 40 std_av
        "stdav": {"stdav": 1, "ml": 10},  # 10ml -> 1 std_av
    }

    def __init__(self, drink_type: str):
        self.drink_type = drink_type

    @property
    def ratio(self) -> float:
        node = self.get_node()
        return 1 / node.get("stdav", 1)

    @property
    def stdav(self) -> float:
        return self.get_node().get("stdav", 1)

    def convert(self, qty: float, drink_type: str) -> float:
        stdav = qty * self.stdav
        node = self.get_node(drink_type)
        return stdav / node.get("stdav", 1)

    def ml_to_stdav(self, ml: int | float, drink_type: str | None = None) -> float:
        node = self.get_node(drink_type)
        return (ml * node["stdav"]) / node["ml"] if node else ml

    def stdav_to_ml(self, stdav: float, drink_type: str | None = None) -> float:
        node = self.get_node(drink_type)
        return (stdav * node["ml"]) / node["stdav"] if node else stdav

    def stdav_to_alcohol(self, stdav: float) -> float:
        # one stdav = 10g pure alkohol (100%)
        return stdav * 0.01

    def stdav_to_bottles(self, year: int, max_stdav: float) -> float:
        days = ydays(year)
        node = self.ratios.get(self.drink_type, {})
        return (max_stdav * days) / node["stdav"] if node else max_stdav * days

    def get_node(self, drink_type: str | None = None):
        if not drink_type:
            drink_type = self.drink_type

        return self.ratios.get(drink_type, {})
