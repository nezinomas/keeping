import re

from django.template import engines
from django_cotton.compiler_regex import CottonCompiler


def _render():
    processed = CottonCompiler().process("<c-quarter-band />")
    return engines["django"].from_string(processed).render({})


def test_four_quarter_cells_span_three_months_each():
    actual = re.findall(r"<th([^>]*)>(.*?)</th>", _render())

    assert actual == [
        (' class="month-table__quarter" colspan="3"', "I ketv."),
        (' class="month-table__quarter" colspan="3"', "II ketv."),
        (' class="month-table__quarter" colspan="3"', "III ketv."),
        (' class="month-table__quarter" colspan="3"', "IV ketv."),
    ]
