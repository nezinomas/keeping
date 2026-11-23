import re

import pytest

from ..utils import render_cotton


@pytest.mark.parametrize("name", ["caption", "body", "foot"])
def test_a_page_value_named_like_a_slot_stays_out_of_the_table(name):
    actual = render_cotton(
        '<c-paper-table><c-slot name="head"><tr></tr></c-slot>'
        "<tr><td>row</td></tr></c-paper-table>",
        **{name: "page value"},
    )

    assert "page value" not in actual
    assert re.search(r"<tbody>\s*<tr><td>row</td></tr>\s*</tbody>", actual)
