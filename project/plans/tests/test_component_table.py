import pytest
from django.http import HttpResponse
from django.template import loader


def _remove_line_end(rendered):
    return str(rendered).replace("\n", "")


@pytest.fixture(name="table")
def fixture_table(fake_request):
    def _func(ctx):
        template = loader.get_template("cotton/plans_table.html")

        return (
            HttpResponse(template.render(ctx, fake_request))
            .content.decode("utf-8")
            .replace("\n", "")
            .replace("\t", "")
            .replace("  ", "")
        )

    return _func


def test_has_type(table):
    context = {"items": [type("O", (object,), dict(january=11))], "type": "TypeRowName"}

    actual = table(context)

    assert '<td class="text-left">TypeRowName</td>' in actual


def test_has_type_and_has_expenses_type(table):
    context = {
        "items": [type("O", (object,), dict(january=11, expense_type="ExpenseType"))],
        "type": "TypeRowName",
        "expense_type": True,
    }

    actual = table(context)

    assert '<td class="text-left">TypeRowName (ExpenseType)</td>' in actual


def test_no_type(table):
    context = {"items": [type("O", (object,), dict(january=11))]}

    actual = table(context)

    assert '<td class="text-left">type</td>' in actual


def test_necessary_expense_1(table):
    context = {
        "items": [
            type("O", (object,), dict(january=11, expense_type=dict(necessary=True)))
        ],
        "type": "TypeRowName",
    }

    actual = table(context)
    expect = (
        '<td class="text-left">TypeRowName <i class="bi bi-star plans-star"></i></td>'
    )

    assert expect in _remove_line_end(actual)


def test_necessary_expense_3(table):
    context = {
        "items": [type("O", (object,), dict(january=11, saving_type=dict(title="xxx")))]
    }

    actual = table(context)
    expect = '<td class="text-left">type <i class="bi bi-star plans-star"></i></td>'

    assert expect in _remove_line_end(actual)


def test_no_object_1(table):
    context = {"year": 2019, "items": []}

    actual = table(context)
    expect = "<b>2019</b> metais įrašų nėra."

    assert expect in _remove_line_end(actual)


def test_no_object_2(table):
    context = {"year": 2019, "items": None}

    actual = table(context)
    expect = "<b>2019</b> metais įrašų nėra."

    assert expect in _remove_line_end(actual)
