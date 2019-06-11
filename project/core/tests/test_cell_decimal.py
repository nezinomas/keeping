import pytest
from django.template import Context, Template

from ...core.tests.utils import _remove_line_end
from ..templatetags.cell_decimal import td


@pytest.fixture()
def _template():
    template_to_render = Template(
        '{% load cell_decimal %}'
        '{% td value %}'
    )
    return template_to_render


def test_cell_positive(_template):
    context = Context({'value': '25'})

    actual = _template.render(context)
    expect = '<td class="text-right " width="7%">25.00</td>'

    assert _remove_line_end(actual) == expect


def test_cell_negative(_template):
    context = Context({'value': '-0.5'})

    actual = _template.render(context)
    expect = '<td class="text-right table-danger" width="7%">-0.50</td>'

    assert _remove_line_end(actual) == expect


def test_cell_intcomma(_template):
    context = Context({'value': '1200'})

    actual = _template.render(context)
    expect = '<td class="text-right " width="7%">1,200.00</td>'

    assert _remove_line_end(actual) == expect


def test_cell_empty(_template):
    context = Context({'value': None})

    actual = _template.render(context)
    expect = '<td class="text-right " width="7%">-</td>'

    assert _remove_line_end(actual) == expect
