import re

import pytest
from django.template import engines
from django_cotton.compiler_regex import CottonCompiler


@pytest.mark.parametrize("name", ["caption", "body", "foot"])
def test_a_page_value_named_like_a_slot_stays_out_of_the_table(name):
    template = engines["django"].from_string(
        CottonCompiler().process(
            '<c-paper-table><c-slot name="head"><tr></tr></c-slot>'
            "<tr><td>row</td></tr></c-paper-table>"
        )
    )

    actual = template.render({name: "page value"})

    assert "page value" not in actual
    assert re.search(r"<tbody>\s*<tr><td>row</td></tr>\s*</tbody>", actual)
