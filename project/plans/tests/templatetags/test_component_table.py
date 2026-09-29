import pytest
from django.template import loader
from django.urls import reverse


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

    context = {
        "kind": "necessary",
        "object_list": {(expense_type, title_str): {}},
    }

    actual = table(context)

    assert "Insurance (Car)" in actual
    assert '<i class="bi bi-star plans-star"></i>' in actual


def test_renders_necessary_plan_urls(table):
    class MockExpenseType:
        id = 5
        title = "Car"

    expense_type = MockExpenseType()
    title_str = "Insurance"

    context = {
        "kind": "necessary",
        "year": 2026,
        "update": "plans:necessary_update",
        "delete": "plans:necessary_delete",
        "object_list": {(expense_type, title_str): {}},
    }

    actual = table(context)

    expect_update = reverse("plans:necessary_update", args=[2026, 5, "Insurance"])
    expect_delete = reverse("plans:necessary_delete", args=[2026, 5, "Insurance"])

    assert expect_update in actual
    assert expect_delete in actual


def test_renders_saving_plan_star(table):
    context = {
        "kind": "saving",
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


def test_renders_no_residual_wash_for_string_title(table):
    context = {"object_list": {"8. Likutis (3 - 7 * dienų)": {}}}

    actual = table(context)

    assert "plans-residual-row" not in actual


def test_renders_no_residual_wash_for_object_title_attribute(table):
    class MockCalculationRow:
        title = "Likutis"

        def __str__(self):
            return "Likutis"

    context = {"object_list": {MockCalculationRow(): {}}}

    actual = table(context)

    assert "plans-residual-row" not in actual


def test_renders_month_headers_full_and_short(table):
    context = {"object_list": {}}

    actual = table(context)

    assert '<span class="plans-table__month-full">Sausis</span>' in actual
    assert '<span class="plans-table__month-short">sau</span>' in actual
    assert '<span class="plans-table__month-full">Rugsėjis</span>' in actual
    assert '<span class="plans-table__month-short">rugs</span>' in actual


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


def test_renders_over_class_only_on_the_over_months(table):
    context = {
        "object_list": {"Dienos planas": {}},
        "states": {"1": "over", "2": "within"},
    }

    actual = table(context)

    assert actual.count("plans-table__over") == 1


def test_renders_no_over_class_without_states(table):
    context = {"object_list": {"Dienos planas": {}}}

    actual = table(context)

    assert "plans-table__over" not in actual
