import pytest
from django.template import Context, Template


def _remove_line_end(rendered):
    return str(rendered).replace("\n", "")


@pytest.fixture(name="template")
def fixture_template():
    return Template(
        "{% load generic_list %}"
        '{% generic_list year=2019 items=items type="type" update=url_update %}'
    )


@pytest.fixture(name="template_with_expenses_type")
def fixture_template_with_expenses_type():
    return Template(
        "{% load generic_list %}"
        '{% generic_list year=2019 items=items type="type" expense_type="True" update=url_update %}'  # noqa: E501
    )


def test_has_type(template):
    items = [type("O", (object,), dict(january=11, type="TypeRowName"))]
    context = Context({"items": items})

    actual = template.render(context).replace("\n", "").replace("  ", "")

    assert '<td class="text-left">TypeRowName</td>' in actual


def test_has_type_and_has_expenses_type(template_with_expenses_type):
    items = [
        type(
            "O",
            (object,),
            dict(january=11, type="TypeRowName", expense_type="ExpenseType"),
        )
    ]
    context = Context({"items": items})

    actual = (
        template_with_expenses_type.render(context).replace("\n", "").replace("  ", "")
    )

    assert '<td class="text-left">TypeRowName (ExpenseType)</td>' in actual


def test_no_type(template):
    items = [type("O", (object,), dict(january=11))]
    context = Context({"items": items})

    actual = template.render(context).replace("\n", "").replace("  ", "")

    assert '<td class="text-left">type</td>' in actual


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
        '<td class="text-left">TypeRowName <i class="bi bi-star plans-star"></i></td>'
    )

    assert expect in _remove_line_end(actual)


def test_necessary_expense_3(template):
    items = [type("O", (object,), dict(january=11, saving_type=dict(title="xxx")))]
    context = Context({"items": items})

    actual = template.render(context).replace("\n", "").replace("  ", "")
    expect = '<td class="text-left">type <i class="bi bi-star plans-star"></i></td>'

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
