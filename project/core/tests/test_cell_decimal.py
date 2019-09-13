import pytest
from django.template import Context, Template

from ...core.tests.utils import _remove_line_end
from ..templatetags.cell_decimal import cell


@pytest.fixture()
def _template():
    template_to_render = Template(
        '{% load cell_decimal %}'
        '{% cell value %}'
    )
    return template_to_render


@pytest.fixture()
def _template_positive_and_negative():
    template_to_render = Template(
        '{% load cell_decimal %}'
        '{% cell value highlight_value=True %}'
    )
    return template_to_render


def test_cell_positive_and_negative_neg(_template_positive_and_negative):
    context = Context({'value': '-0.5'})

    actual = _template_positive_and_negative.render(context)
    expect = '<td class="table-danger" >-0,50</td>'

    assert _remove_line_end(actual) == expect


def test_cell_positive_and_negative_pos(_template_positive_and_negative):
    context = Context({'value': '0.5'})

    actual = _template_positive_and_negative.render(context)
    expect = '<td class="table-success" >0,50</td>'


def test_cell_intcomma(_template):
    context = Context({'value': '1200'})

    actual = _template.render(context)
    expect = '<td class="" >1 200,00</td>'

    assert _remove_line_end(actual) == expect


def test_cell_empty(_template):
    context = Context({'value': None})

    actual = _template.render(context)
    expect = '<td class="" ></td>'

    assert _remove_line_end(actual) == expect
