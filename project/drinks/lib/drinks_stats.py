from typing import Dict, List


class DrinkStats():
    def __init__(self, arr: List[Dict]):
        _list = [0.0 for x in range(0, 12)]

        self._consumsion = _list.copy()
        self._quantity = _list.copy()

        self._calc(arr)

    @property
    def consumsion(self) -> List[float]:
        return self._consumsion

    @property
    def quantity(self) -> List[float]:
        return self._quantity

    def _calc(self, arr: List[Dict]) -> None:
        if not arr:
            return

        for a in arr:
            idx = a.get('month', 1) - 1

            self._consumsion[idx] = a.get('per_month', 0)
            self._quantity[idx] = a.get('sum', 0)
