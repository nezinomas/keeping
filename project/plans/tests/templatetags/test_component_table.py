import re

import pytest

from ....core.tests.utils import render_cotton
from ...services.plan_rows import PlanRow

ALL_WITHIN = ["within"] * 12


def _without_breaks_or_indents(rendered):
    return str(rendered).replace("\n", "").replace("    ", "").replace("  ", "")


@pytest.fixture(name="table")
def fixture_table():
    def _render_plans_table(rows, year=2026):
        return _without_breaks_or_indents(
            render_cotton(
                '<c-plans-table :rows="rows" :year="year" />', rows=rows, year=year
            )
        )

    return _render_plans_table


def _row(title="Salary", states=ALL_WITHIN):
    return PlanRow(
        title=title,
        update_url="/update/",
        delete_url="/delete/",
        cells=[(0, state) for state in states],
    )


def test_renders_a_row_with_its_title(table):
    actual = table([_row("Salary")])

    assert "<td>Salary</td>" in actual


def test_the_empty_row_spans_the_header_and_closes(table):
    actual = table([])

    columns = actual.split("</thead>")[0].split("<tr>")[-1]
    body = actual.split("<tbody>")[1].split("</tbody>")[0]
    assert len(re.findall(r"<th[ >]", columns)) == 15
    assert re.findall(r"<td([^>]*)>(.*?)</td>", body) == [
        (' colspan="15"', "2026 metais įrašų nėra.")
    ]


@pytest.mark.parametrize(
    "states, count",
    [
        pytest.param(["over"] + ALL_WITHIN[1:], 1, id="one_over"),
        pytest.param(ALL_WITHIN, 0, id="all_within"),
    ],
)
def test_renders_over_class_only_on_the_over_months(table, states, count):
    actual = table([_row(states=states)])

    assert (
        len(re.findall(r'<td class="main__figure plans-table__over"', actual)) == count
    )


def test_draws_its_table_shell(table):
    actual = table([_row()])

    assert '<table class="main striped hover">' in actual


def test_heads_its_title_column_and_its_edit_and_delete_columns(table):
    head = table([_row()]).split("</thead>")[0].split("<tr>")[-1]
    cells = re.findall(r"<th([^>]*)>([^<]*)</th>", head)

    assert [cells[0], *cells[-2:]] == [
        ("", "Pavadinimas"),
        (' class="edit-col"', ""),
        (' class="delete-col"', ""),
    ]
