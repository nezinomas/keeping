import re

import pytest

from ....core.tests.utils import render_cotton

# the page's own values under the names a cell's options read
PAGE = {
    "value": 5678,
    "colspan": 3,
    "signed": True,
    "ok": True,
    "show": "open",
    "empty": True,
    "group": True,
}


@pytest.mark.parametrize(
    "source, cell",
    [
        pytest.param(
            '<c-figure-cell :value="figure" />',
            '<td class="main__figure" data-cell="">12,34</td>',
            id="its-value",
        ),
        pytest.param(
            "<c-figure-cell />",
            '<td class="main__figure" data-cell="empty">-</td>',
            id="no-value",
        ),
    ],
)
def test_a_figure_cell_draws_nothing_it_is_not_given(source, cell):
    content = render_cotton(source, figure=1234, **PAGE)

    assert re.findall(r"<td\b[^>]*>[^<]*</td>", content) == [cell]
