import re

import pytest
from django.template import Context, Template

from .utils import clean_content


@pytest.fixture()
def _template():
    return Template(
        '{% load slippers %}'
        '{% table_cell value=value %}'
    )


@pytest.fixture()
def _template_positive_and_negative():
    return Template(
        '{% load slippers %}'
        '{% table_cell value=value highlight_value=True %}'
    )


def test_cell_positive_and_negative_neg(_template_positive_and_negative):
    context = Context({'value': '-0,5'})

    actual = _template_positive_and_negative.render(context)
    expect = '<td class="table-danger">-0,50</td>'

    actual = clean_content(actual)
    actual = re.sub(r'\s{2,}', '', actual)

    assert actual == expect


def test_cell_positive_and_negative_pos(_template_positive_and_negative):
    context = Context({'value': '0,5'})

    expect = '<td class="table-success">0,50</td>'

    actual = _template_positive_and_negative.render(context)
    actual = clean_content(actual)
    actual = re.sub(r'\s{2,}', '', actual)

    assert actual == expect


def test_cell_intcomma(_template):
    context = Context({'value': '1200'})

    expect = '<td class="">1.200,00</td>'

    actual = _template.render(context)
    actual = clean_content(actual)
    actual = re.sub(r'\s{2,}', '', actual)

    assert actual == expect


def test_cell_empty(_template):
    context = Context({'value': None})

    actual = _template.render(context)
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


def test_cell_float_zero(_template):
    context = Context({'value': 0.0})

    actual = _template.render(context)
    expect = '<td class=" dash">-</td>'

    actual = clean_content(actual)
    actual = re.sub(r'\s{2,}', '', actual)

    assert actual == expect


def test_cell_string_zero(_template):
    context = Context({'value': '0'})

    actual = _template.render(context)
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
