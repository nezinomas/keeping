from ...lib.calc_day_sum import MONTH_NUMS as MONTHS
from ...lib.calc_day_sum import DataDto, PlanCalculateDaySum
from ...services.calculations import Calculations


def _months(amounts):
    return [{"month": i + 1, "amount": amount} for i, amount in enumerate(amounts)]


def _full_data():
    per_day = [20] * 10 + [40, 0]

    return DataDto(
        incomes=_months([1000] * 12),
        expenses_regular=_months([80] * 12),
        expenses_necessary=_months([100] * 12),
        savings=_months([50] * 12),
        per_day=_months(per_day),
        necessary=_months([50] * 12),
        month_len=_months([30] * 12),
    )


def _p18_data():
    return DataDto(
        incomes=[
            {"month": 1, "amount": 900},
            {"month": 2, "amount": 1000},
            {"month": 3, "amount": 450},
            {"month": 4, "amount": 450},
            {"month": 5, "amount": 450},
            {"month": 6, "amount": 450},
            {"month": 7, "amount": 450},
            {"month": 8, "amount": 450},
            {"month": 9, "amount": 450},
            {"month": 10, "amount": 450},
            {"month": 11, "amount": 450},
            {"month": 12, "amount": 450},
        ],
        expenses_regular=[
            {"month": 1, "amount": 260},
            {"month": 2, "amount": 280},
        ],
        expenses_necessary=[
            {"month": 1, "amount": 300},
            {"month": 2, "amount": 320},
        ],
        savings=[
            {"month": 1, "amount": 190},
            {"month": 2, "amount": 200},
        ],
        per_day=[
            {"month": 1, "amount": 25},
            {"month": 2, "amount": 26},
        ],
        necessary=[
            {"month": 2, "amount": 100},
        ],
        month_len=[
            {"month": 1, "amount": 31},
            {"month": 2, "amount": 29},
            {"month": 3, "amount": 31},
            {"month": 4, "amount": 30},
            {"month": 5, "amount": 31},
            {"month": 6, "amount": 30},
            {"month": 7, "amount": 31},
            {"month": 8, "amount": 31},
            {"month": 9, "amount": 30},
            {"month": 10, "amount": 31},
            {"month": 11, "amount": 30},
            {"month": 12, "amount": 31},
        ],
    )


def _blocks():
    return Calculations.build(PlanCalculateDaySum(_full_data()))


def _rows(blocks):
    return [row for block in blocks for row in block.rows]


def test_block_titles_in_order():
    blocks = _blocks()

    assert [block.title for block in blocks] == [
        "Kiek galiu išleisti per dieną",
        "Patikra: ar telpa išlaidų planai",
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


def test_part_rows_come_right_after_the_necessary_expenses_and_savings_row():
    blocks = _blocks()
    labels = [row.label for row in _rows(blocks)]
    total_index = labels.index("Būtinos išlaidos ir taupymas")

    assert labels[total_index + 1 : total_index + 4] == [
        "Būtinos išlaidos",
        "Papildomos būtinos išlaidos",
        "Taupymas",
    ]


def test_p18_guard_rows_match_plans_stats():
    day_sum = PlanCalculateDaySum(_p18_data())
    blocks = Calculations.build(day_sum)
    by_label = {row.label: row for row in _rows(blocks)}
    old = list(day_sum.plans_stats().values())

    mapping = {
        "Pajamos": old[0],
        "Būtinos išlaidos ir taupymas": old[1],
        "Laisvi pinigai": old[2],
        "Kasdienės išlaidos pagal planą": old[3],
        "Visos išlaidos": old[4],
        "Lieka po išlaidų planų": old[5],
        "Suma dienai": old[6],
        "Likutis": old[7],
    }

    for label, old_row in mapping.items():
        for month in MONTHS:
            assert by_label[label].values[int(month) - 1] == old_row[month], (
                label,
                month,
            )


def test_part_rows_sum_to_necessary_expenses_and_savings():
    blocks = _blocks()
    by_label = {row.label: row for row in _rows(blocks)}
    necessary = by_label["Būtinos išlaidos"]
    additional = by_label["Papildomos būtinos išlaidos"]
    savings = by_label["Taupymas"]
    total = by_label["Būtinos išlaidos ir taupymas"]

    for i in range(12):
        assert (
            necessary.values[i] + additional.values[i] + savings.values[i]
            == total.values[i]
        )


def test_only_day_plan_row_has_over_states():
    blocks = _blocks()
    by_label = {row.label: row for row in _rows(blocks)}
    day_sum = PlanCalculateDaySum(_full_data())
    expected_over_months = {
        month for month, state in day_sum.day_plan_states().items() if state == "over"
    }

    for label, row in by_label.items():
        over_months = {
            MONTHS[i] for i, state in enumerate(row.states) if state == "over"
        }
        if label == "Dienos planas":
            assert over_months == expected_over_months
        else:
            assert over_months == set()


def test_residual_has_no_state_even_when_negative():
    blocks = _blocks()
    by_label = {row.label: row for row in _rows(blocks)}
    residual = by_label["Likutis"]

    assert any(value < 0 for value in residual.values)
    assert set(residual.states) == {"within"}


def test_part_is_true_for_exactly_three_rows():
    blocks = _blocks()

    part_labels = [row.label for row in _rows(blocks) if row.part]

    assert part_labels == [
        "Būtinos išlaidos",
        "Papildomos būtinos išlaidos",
        "Taupymas",
    ]
