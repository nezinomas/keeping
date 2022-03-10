from ...core.lib import utils


class DrinksOptions():
    def __init__(self, drink_type: str = None):
        if not drink_type:
            drink_type = utils.get_user().drink_type

        self._drink_type = drink_type

    @property
    def ratio(self) -> float:
        ratios = {
            'beer': DrinksOptions.std_to_beer(1),
            'wine': DrinksOptions.std_to_wine(1),
            'vodka': DrinksOptions.std_to_vodka(1)
        }

        return ratios.get(self._drink_type, 1)

    @staticmethod
    def std_to_beer(av: float) -> float:
        # one 500ml bottle ~ 2.5 std av
        return av * 0.4

    @staticmethod
    def beer_to_std(av: float) -> float:
        # one 500ml bottle ~ 2.5 std av
        return av / 0.4

    @staticmethod
    def std_to_wine(av: float) -> float:
        # one 750ml bottle ~ 8 std av
        return av * 0.125

    @staticmethod
    def wine_to_std(av: float) -> float:
        # one 750ml bottle ~ 8 std av
        return av / 0.125

    @staticmethod
    def std_to_vodka(av: float) -> float:
        # one 1000ml bottle ~ 40 std av
        return av * 0.025

    @staticmethod
    def vodka_to_std(av: float) -> float:
        # one 1000ml bottle ~ 40 std av
        return av / 0.025
