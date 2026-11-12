from types import SimpleNamespace

import pytest
from django.template.loader import render_to_string
from django.urls import NoReverseMatch


@pytest.mark.parametrize(
    "names", [{}, {"url_name": "savings:nowhere"}], ids=["missing", "unknown"]
)
def test_an_owner_table_without_a_url_name_that_reverses_raises(names):
    rows = [SimpleNamespace(pk=1, title="Fund")]

    with pytest.raises(NoReverseMatch):
        render_to_string("core/closed_fold.html", {"rows": rows, **names})
