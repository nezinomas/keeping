import re

import pytest
from django.template import engines
from django_cotton.compiler_regex import CottonCompiler

from ...services.plan_rows import PlanRow

ALL_WITHIN = ["within"] * 12


def _remove_line_end(rendered):
    return str(rendered).replace("\n", "").replace("    ", "").replace("  ", "")


@pytest.fixture(name="table")
def fixture_table():
    def _func(rows, year=2026):
        processed = CottonCompiler().process(
            '<c-plans-table :rows="rows" :year="year" />'
        )
        template = engines["django"].from_string(processed)
        return _remove_line_end(template.render({"rows": rows, "year": year}))

    return _func


def _row(title="Salary", states=ALL_WITHIN):
    return PlanRow(
        title=title,
        update_url="/update/",
        delete_url="/delete/",
        cells=[(0, state) for state in states],
    )


def test_renders_a_row_with_its_title(table):
    actual = table([_row("Salary")])

    assert '<td class="text-left">Salary</td>' in actual


def test_the_empty_row_spans_the_header_and_closes(table):
    actual = table([])

    header = actual.split("<thead>")[1].split("</thead>")[0]
    body = actual.split("<tbody>")[1].split("</tbody>")[0]
    assert len(re.findall(r"<th[ >]", header)) == 15
    assert re.findall(r"<td([^>]*)>(.*?)</td>", body) == [
        (' colspan="15"', "<b>2026</b> metais įrašų nėra.")
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

    assert actual.count("plans-table__over") == count
