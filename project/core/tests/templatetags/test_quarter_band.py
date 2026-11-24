import re

from ..utils import render_cotton


def test_four_quarter_cells_span_three_months_each():
    actual = re.findall(r"<th([^>]*)>(.*?)</th>", render_cotton("<c-quarter-band />"))

    assert actual == [
        (' class="month-table__quarter" colspan="3"', "I ketv."),
        (' class="month-table__quarter" colspan="3"', "II ketv."),
        (' class="month-table__quarter" colspan="3"', "III ketv."),
        (' class="month-table__quarter" colspan="3"', "IV ketv."),
    ]
