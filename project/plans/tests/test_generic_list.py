import pytest
from django.template import Context, Template


def _remove_line_end(rendered):
    return str(rendered).replace('\n', '')


@pytest.fixture()
def _template():
    template_to_render = Template(
        '{% load generic_list %}'
        '{% generic_list items "url_update" 2019 "type" %}'
    )
    return template_to_render


def test_has_type(_template):
    items = [type('O', (object,), dict(january=11, type='TypeRowName'))]
    context = Context({'items': items})

    actual = _template.render(context)

    assert '<td class="text-start">TypeRowName</td>' in actual


def test_no_type(_template):
    items = [type('O', (object,), dict(january=11))]
    context = Context({'items': items})

    actual = _template.render(context)

    assert '<td class="text-start">type</td>' in actual


def test_necessary_expense_1(_template):
    items = [
        type(
            'O',
            (object,),
            dict(january=11, type='TypeRowName', expense_type=dict(necessary=True))
        )
    ]
    context = Context({'items': items})

    actual = _template.render(context)
    expect = '<td class="text-start">TypeRowName <i class="bi bi-star plans-star"></i></td>'

    assert expect in _remove_line_end(actual)


def test_necessary_expense_3(_template):
    items = [
        type(
            'O',
            (object,),
            dict(january=11, saving_type=dict(title='xxx'))
        )
    ]
    context = Context({'items': items})

    actual = _template.render(context)
    expect = '<td class="text-start">type <i class="bi bi-star plans-star"></i></td>'

    assert expect in _remove_line_end(actual)


def test_no_object_1(_template):
    items = []
    context = Context({'items': items})

    actual = _template.render(context)
    expect = '<b>2019</b> metais įrašų nėra.'

    assert expect in _remove_line_end(actual)


def test_no_object_2(_template):
    items = None
    context = Context({'items': items})

    actual = _template.render(context)
    expect = '<b>2019</b> metais įrašų nėra.'

    assert expect in _remove_line_end(actual)
