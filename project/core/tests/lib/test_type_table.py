from datetime import date

import pytest

from ...lib.type_table import Cells, Figures, Total


@pytest.mark.parametrize(
    "figures, expected",
    [
        (
            Figures(900_000, 800_000, [date(2026, 9, 10)]),
            ("9.000", "8.000", "75%", "2026-09-10"),
        ),
        (Figures(0, 0, []), ("–", "–", "–", "–")),
    ],
    ids=["whole_euros", "a_type_without_records_reads_dashes"],
)
def test_cells_state_a_rows_figures(figures, expected):
    cells = Cells(1, "Alga", ("alga",), figures, share_of=1_200_000)

    assert (cells.this_year, cells.last_year, cells.share, cells.last_date) == expected


@pytest.mark.parametrize(
    "figures, expected",
    [
        (
            [Figures(900_000, 800_000, []), Figures(300_000, 0, [])],
            ("12.000", "8.000", "100%"),
        ),
        ([], ("–", "–", "–")),
    ],
    ids=["every_type_summed", "empty_year"],
)
def test_the_total_sums_each_column(figures, expected):
    total = Total.of(Figures.summed(figures))

    assert (total.this_year, total.last_year, total.share) == expected
