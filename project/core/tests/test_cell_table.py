import re

import pytest
from django.template import Context, Template

from .utils import clean_content


@pytest.fixture(name="template")
def fixture_template():
    return Template(
        '{% load slippers %}'
        '{% table_cell value=value %}'
    )


@pytest.fixture(name="template_for_highlight")
def fixture_template_for_highlight():
    return Template(
        '{% load slippers %}'
        '{% table_cell value=value highlight_value=True %}'
    )


def test_cell_positive_and_negative_neg(template_for_highlight):
    context = Context({'value': '-0,5'})

    actual = template_for_highlight.render(context)
    expect = '<td class="table-danger">-0,50</td>'

    actual = clean_content(actual)
    actual = re.sub(r'\s{2,}', '', actual)

    assert actual == expect


def test_cell_positive_and_negative_pos(template_for_highlight):
    context = Context({'value': '0,5'})

    expect = '<td class="table-success">0,50</td>'

    actual = template_for_highlight.render(context)
    actual = clean_content(actual)
    actual = re.sub(r'\s{2,}', '', actual)

    assert actual == expect


def test_cell_intcomma(template):
    context = Context({'value': '1200'})

    expect = '<td class="">1.200,00</td>'

    actual = template.render(context)
    actual = clean_content(actual)
    actual = re.sub(r'\s{2,}', '', actual)

    assert actual == expect


def test_cell_empty(template):
    context = Context({'value': None})

    actual = template.render(context)
    expect = '<td class=" dash">-</td>'

    actual = clean_content(actual)
    actual = re.sub(r'\s{2,}', '', actual)

    assert actual == expect


@pytest.mark.parametrize(
    'value',
    [None, 'None', '0.0', 0, '0']
)
def test_cell_empty_with_default_if_empty(value):
    template = Template(
        '{% load slippers %}'
        '{% table_cell value=value default_if_empty="OK" %}'
    )
    context = Context({'value': value})

    actual = template.render(context)
    expect = '<td class="">OK</td>'

    actual = clean_content(actual)
    actual = re.sub(r'\s{2,}', '', actual)

    assert actual == expect


def test_cell_float_zero(template):
    context = Context({'value': 0.0})

    actual = template.render(context)
    expect = '<td class=" dash">-</td>'

    actual = clean_content(actual)
    actual = re.sub(r'\s{2,}', '', actual)

    assert actual == expect


def test_cell_string_zero(template):
    context = Context({'value': '0'})

    actual = template.render(context)
    expect = '<td class=" dash">-</td>'

    actual = clean_content(actual)
    actual = re.sub(r'\s{2,}', '', actual)

    assert actual == expect


def test_cell_tag_th():
    tmpl = Template(
        '{% load slippers %}'
        '{% table_cell value=value tag="th" %}'
    )
    context = Context({'value': 1})

    expect = '<th class="">1,00</th>'

    actual = tmpl.render(context)
    actual = clean_content(actual)
    actual = re.sub(r'\s{2,}', '', actual)

    assert actual == expect


def test_cell_tag_td():
    tmpl = Template(
        '{% load slippers %}'
        '{% table_cell value=value %}'
    )
    context = Context({'value': 1})

    expect = '<td class="">1,00</td>'

    actual = tmpl.render(context)
    actual = clean_content(actual)
    actual = re.sub(r'\s{2,}', '', actual)

    assert actual == expect


def test_cell_css_class_one():
    tmpl = Template(
        '{% load slippers %}'
        '{% table_cell value=value css_class="X" %}'
    )
    context = Context({'value': 1})

    expect = '<td class=" X">1,00</td>'

    actual = tmpl.render(context)
    actual = clean_content(actual)
    actual = re.sub(r'\s{2,}', '', actual)

    assert actual == expect


def test_cell_css_class_many():
    tmpl = Template(
        '{% load slippers %}'
        '{% table_cell value=value css_class="X Y Z" %}'
    )
    context = Context({'value': 1})

    expect = '<td class=" X Y Z">1,00</td>'

    actual = tmpl.render(context)
    actual = clean_content(actual)
    actual = re.sub(r'\s{2,}', '', actual)

    assert actual == expect
