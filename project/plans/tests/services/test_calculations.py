import pytest

from ...lib.calc_day_sum import PlanCalculateDaySum
from ...lib.month_states import MONTH_NUMS, OVER
from ...services.calculations import Calculations
from ..day_sum_data import make_data

CENT = 0.005


def _blocks():
    return Calculations.build(PlanCalculateDaySum(make_data()))


def _rows(blocks):
    return [row for block in blocks for row in block.rows]


def test_blocks_in_order():
    assert [(block.key, block.title) for block in _blocks()] == [
        ("spend", "Kiek galiu išleisti per dieną"),
        ("check", "Patikra: ar telpa išlaidų planai"),
    ]


def test_row_labels_in_order():
    blocks = _blocks()

    assert [row.label for row in _rows(blocks)] == [
        "Pajamos",
        "Būtinos išlaidos ir taupymas",
        "Būtinos išlaidos",
        "Papildomos būtinos išlaidos",
        "Taupymas",
        "Laisvi pinigai",
        "Suma dienai",
        "Dienos planas",
        "Likutis",
        "Kasdienės išlaidos pagal planą",
        "Visos išlaidos",
        "Lieka po išlaidų planų",
    ]


# make_data's first three months: January and February differ, March stands for the rest
@pytest.mark.parametrize(
    "label, values, over",
    [
        ("Pajamos", [450, 450, 450], []),
        ("Būtinos išlaidos ir taupymas", [490, 620, 0], []),
        ("Būtinos išlaidos", [300, 320, 0], []),
        ("Papildomos būtinos išlaidos", [0, 100, 0], []),
        ("Taupymas", [190, 200, 0], []),
        ("Laisvi pinigai", [-40, -170, 450], []),
        ("Suma dienai", [-1.29, -5.86, 14.52], []),
        ("Dienos planas", [25, 26, 0], ["1", "2"]),
        ("Likutis", [-815, -924, 450], []),
        ("Kasdienės išlaidos pagal planą", [260, 280, 0], []),
        ("Visos išlaidos", [750, 900, 0], []),
        ("Lieka po išlaidų planų", [-300, -450, 450], []),
    ],
)
def test_row_values_and_over_months(label, values, over):
    row = {row.label: row for row in _rows(_blocks())}[label]

    assert row.values[:3] == pytest.approx(values, abs=CENT)
    assert [month for month, state in zip(MONTH_NUMS, row.states) if state == OVER] == (
        over
    )


def test_part_is_true_for_exactly_three_rows():
    blocks = _blocks()

    part_labels = [row.label for row in _rows(blocks) if row.part]

    assert part_labels == [
        "Būtinos išlaidos",
        "Papildomos būtinos išlaidos",
        "Taupymas",
    ]
