import pytest
from django.template import Context, Template

from ...core.tests.utils import _remove_line_end
from ..templatetags.table_cell import cell


@pytest.fixture()
def _template():
    template_to_render = Template(
        '{% load table_cell %}'
        '{% cell value %}'
    )
    return template_to_render


@pytest.fixture()
def _template_positive_and_negative():
    template_to_render = Template(
        '{% load table_cell %}'
        '{% cell value highlight_value=True %}'
    )
    return template_to_render


def test_cell_positive_and_negative_neg(_template_positive_and_negative):
    context = Context({'value': '-0.5'})

    actual = _template_positive_and_negative.render(context)
    expect = '<td class="table-danger">-0,50</td>'

    assert _remove_line_end(actual) == expect


def test_cell_positive_and_negative_pos(_template_positive_and_negative):
    context = Context({'value': '0.5'})

    actual = _template_positive_and_negative.render(context)
    expect = '<td class="table-success">0,50</td>'


def test_cell_intcomma(_template):
    context = Context({'value': '1200'})

    actual = _template.render(context)
    expect = '<td class="">1.200,00</td>'

    assert _remove_line_end(actual) == expect


def test_cell_empty(_template):
    context = Context({'value': None})

    actual = _template.render(context)
    expect = '<td class=" dash">-</td>'

    assert _remove_line_end(actual) == expect


def test_cell_float_zero(_template):
    context = Context({'value': 0.0})

    actual = _template.render(context)
    expect = '<td class=" dash">-</td>'

    assert _remove_line_end(actual) == expect


def test_cell_string_zero(_template):
    context = Context({'value': '0'})

    actual = _template.render(context)
    expect = '<td class=" dash">-</td>'

    assert _remove_line_end(actual) == expect


def test_cell_tag_th():
    tmpl = Template(
        '{% load table_cell %}'
        '{% cell value tag="th" %}'
    )
    context = Context({'value': 1})

    expect = '<th class="">1,00</th>'

    actual = tmpl.render(context)

    assert _remove_line_end(actual) == expect


def test_cell_tag_td():
    tmpl = Template(
        '{% load table_cell %}'
        '{% cell value %}'
    )
    context = Context({'value': 1})

    expect = '<td class="">1,00</td>'

    actual = tmpl.render(context)

    assert _remove_line_end(actual) == expect


def test_cell_css_class_one():
    tmpl = Template(
        '{% load table_cell %}'
        '{% cell value css_class="X" %}'
    )
    context = Context({'value': 1})

    expect = '<td class=" X">1,00</td>'

    actual = tmpl.render(context)

    assert _remove_line_end(actual) == expect


def test_cell_css_class_many():
    tmpl = Template(
        '{% load table_cell %}'
        '{% cell value css_class="X Y Z" %}'
    )
    context = Context({'value': 1})

    expect = '<td class=" X Y Z">1,00</td>'

    actual = tmpl.render(context)

    assert _remove_line_end(actual) == expect
