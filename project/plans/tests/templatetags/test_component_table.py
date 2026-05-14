from types import SimpleNamespace

import pytest
from django.template import loader


def _remove_line_end(rendered):
    return str(rendered).replace("\n", "").replace("    ", "").replace("  ", "")


@pytest.fixture(name="table")
def fixture_table(fake_request):
    def _func(ctx):
        template = loader.get_template("cotton/plans_table.html")
        return _remove_line_end(template.render(ctx, fake_request))

    return _func


def test_renders_standard_row(table):
    context = {
        "object_list": {"Salary": {}},
    }

    actual = table(context)

    assert '<td class="text-left">Salary</td>' in actual


def test_renders_necessary_plan_tuple_format(table):
    class MockExpenseType:
        title = "Car"

    expense_type = MockExpenseType()
    title_str = "Insurance"

    view = SimpleNamespace(plan_type="necessary")
    context = {
        "view": view,
        "object_list": {(expense_type, title_str): {}},
    }

    actual = table(context)

    assert "Insurance (Car)" in actual
    assert '<i class="bi bi-star plans-star"></i>' in actual


def test_renders_saving_plan_star(table):
    view = SimpleNamespace(plan_type="saving")
    context = {
        "view": view,
        "object_list": {"Emergency Fund": {}},
    }

    actual = table(context)

    assert "Emergency Fund" in actual
    assert '<i class="bi bi-star plans-star"></i>' in actual


def test_renders_object_with_necessary_attribute(table):
    class MockExpense:
        necessary = True

        def __str__(self):
            return "Food"

    context = {
        "object_list": {MockExpense(): {}},
    }

    actual = table(context)

    assert "Food" in actual
    assert '<i class="bi bi-star plans-star"></i>' in actual


def test_renders_empty_state_correctly(table):
    context = {"year": 2026, "object_list": {}}

    actual = table(context)

    expect = "<b>2026</b> metais įrašų nėra."
    assert expect in actual


def test_renders_none_state_correctly(table):
    context = {"year": 2026, "object_list": None}

    actual = table(context)

    expect = "<b>2026</b> metais įrašų nėra."
    assert expect in actual
