import pytest
from django.template import Context, Template


def _remove_line_end(rendered):
    return str(rendered).replace("\n", "")


@pytest.fixture(name="template")
def fixturetemplate():
    template_to_render = Template(
        "{% load generic_list %}"
        '{% generic_list year=2019 items=items type="type" update=url_update %}'
    )
    return template_to_render


def test_has_type(template):
    items = [type("O", (object,), dict(january=11, type="TypeRowName"))]
    context = Context({"items": items})

    actual = template.render(context).replace("\n", "").replace("  ", "")

    assert '<td class="text-start">TypeRowName</td>' in actual


def test_no_type(template):
    items = [type("O", (object,), dict(january=11))]
    context = Context({"items": items})

    actual = template.render(context).replace("\n", "").replace("  ", "")

    assert '<td class="text-start">type</td>' in actual


def test_necessary_expense_1(template):
    items = [
        type(
            "O",
            (object,),
            dict(january=11, type="TypeRowName", expense_type=dict(necessary=True)),
        )
    ]
    context = Context({"items": items})

    actual = template.render(context).replace("\n", "").replace("  ", "")
    expect = (
        '<td class="text-start">TypeRowName <i class="bi bi-star plans-star"></i></td>'
    )

    assert expect in _remove_line_end(actual)


def test_necessary_expense_3(template):
    items = [type("O", (object,), dict(january=11, saving_type=dict(title="xxx")))]
    context = Context({"items": items})

    actual = template.render(context).replace("\n", "").replace("  ", "")
    expect = '<td class="text-start">type <i class="bi bi-star plans-star"></i></td>'

    assert expect in _remove_line_end(actual)


def test_no_object_1(template):
    items = []
    context = Context({"items": items})

    actual = template.render(context)
    expect = "<b>2019</b> metais įrašų nėra."

    assert expect in _remove_line_end(actual)


def test_no_object_2(template):
    items = None
    context = Context({"items": items})

    actual = template.render(context)
    expect = "<b>2019</b> metais įrašų nėra."

    assert expect in _remove_line_end(actual)
