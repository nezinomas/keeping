import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.signals import post_save
from django.utils.translation import gettext as _
from factory.django import mute_signals

from ...expenses.tests.factories import ExpenseTypeFactory
from ...incomes.tests.factories import IncomeTypeFactory
from ...savings.tests.factories import SavingTypeFactory
from ..services.model_services import (
    DayPlanModelService,
    ExpensePlanModelService,
    IncomePlanModelService,
    MonthTargets,
    NecessaryPlanModelService,
    SavingPlanModelService,
)
from .factories import (
    PLAN_KINDS,
    DayPlanFactory,
    ExpensePlanFactory,
    IncomePlanFactory,
    NecessaryPlanFactory,
    SavingPlanFactory,
)

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def mute_my_signals():
    with mute_signals(post_save):
        yield


KINDS = [
    pytest.param(IncomePlanModelService, IncomePlanFactory, id="income"),
    pytest.param(ExpensePlanModelService, ExpensePlanFactory, id="expense"),
    pytest.param(SavingPlanModelService, SavingPlanFactory, id="saving"),
    pytest.param(DayPlanModelService, DayPlanFactory, id="day"),
    pytest.param(NecessaryPlanModelService, NecessaryPlanFactory, id="necessary"),
]


TYPED_KINDS = [
    pytest.param(
        IncomePlanModelService,
        IncomePlanFactory,
        IncomeTypeFactory,
        "income_type",
        ("Salary", "Bonus"),
        id="income",
    ),
    pytest.param(
        ExpensePlanModelService,
        ExpensePlanFactory,
        ExpenseTypeFactory,
        "expense_type",
        ("ZZZ", "AAA"),
        id="expense",
    ),
    pytest.param(
        SavingPlanModelService,
        SavingPlanFactory,
        SavingTypeFactory,
        "saving_type",
        ("ZZZ", "AAA"),
        id="saving",
    ),
]

SERVICES = [
    pytest.param(IncomePlanModelService, id="income"),
    pytest.param(ExpensePlanModelService, id="expense"),
    pytest.param(SavingPlanModelService, id="saving"),
    pytest.param(DayPlanModelService, id="day"),
    pytest.param(NecessaryPlanModelService, id="necessary"),
]


def month_targets(user, type_titles):
    return MonthTargets.for_month(
        type_titles=type_titles,
        expense_plans=ExpensePlanModelService(user).year(1999),
        necessary_plans=NecessaryPlanModelService(user).year(1999),
        saving_plans=SavingPlanModelService(user).year(1999),
        month=2,
    )


def test_targets_fills_zeros_for_empty_plans(main_user):
    ExpenseTypeFactory(title="T1")
    ExpenseTypeFactory(title="T2")

    actual = month_targets(main_user, ["T1", "T2"])

    expect = {"T1": 0, "T2": 0, "savings": 0}

    assert actual == expect


@pytest.mark.parametrize(
    "with_savings, saved",
    [
        pytest.param(True, 300, id="with_savings"),
        pytest.param(False, 0, id="no_savings"),
    ],
)
def test_targets_sums_correctly_and_ignores_other_months(
    main_user, with_savings, saved
):
    t1 = ExpenseTypeFactory(title="T1")
    t2 = ExpenseTypeFactory(title="T2")
    t3 = ExpenseTypeFactory(title="T3")

    ExpensePlanFactory(month=2, expense_type=t1, price=100)
    NecessaryPlanFactory(month=2, expense_type=t1, price=50)
    NecessaryPlanFactory(month=2, expense_type=t2, price=200)
    ExpensePlanFactory(month=3, expense_type=t3, price=999)
    if with_savings:
        SavingPlanFactory(month=2, price=300)
        SavingPlanFactory(month=3, price=999)

    actual = month_targets(main_user, ["T1", "T2", "T3"])

    expect = {"T1": 150, "T2": 200, "T3": 0, "savings": saved}

    assert actual == expect


def test_targets_ignore_unknown_expense_types(main_user):
    t1 = ExpenseTypeFactory(title="T1")
    ExpensePlanFactory(month=2, expense_type=t1, price=100)
    NecessaryPlanFactory(month=2, expense_type=t1, price=50)

    actual = month_targets(main_user, [])

    expect = {"savings": 0}
    assert actual == expect


@pytest.mark.parametrize(
    "factory, kwargs, expect",
    [
        pytest.param(IncomePlanFactory, {}, "2000/Income Type", id="income"),
        pytest.param(ExpensePlanFactory, {}, "2000/Expense Type", id="expense"),
        pytest.param(SavingPlanFactory, {}, "2000/Savings", id="saving"),
        pytest.param(DayPlanFactory, {}, "2000", id="day"),
        pytest.param(NecessaryPlanFactory, {"title": "N"}, "2000/N", id="necessary"),
    ],
)
def test_plan_str(factory, kwargs, expect):
    actual = factory.build(year=2000, **kwargs)

    assert str(actual) == expect


@pytest.mark.parametrize("service, factory", KINDS)
def test_plan_objects_are_the_users_only(main_user, second_user, service, factory):
    factory()
    factory(journal=second_user.journal)

    actual = service(main_user).objects

    assert len(actual) == 1
    assert actual[0].journal.users.first().username == "bob"


@pytest.mark.parametrize("service, factory", KINDS)
def test_plan_year(main_user, second_user, service, factory):
    factory(year=1999, month=1, price=1)
    factory(year=1999, month=2, price=2)
    factory(year=1974, journal=second_user.journal)

    actual = list(service(main_user).year(1999))

    assert len(actual) == 2
    assert actual[0].year == 1999
    assert actual[0].journal.users.first().username == "bob"
    assert actual[0].month == 1
    assert actual[0].price == 1

    assert actual[1].year == 1999
    assert actual[1].journal.users.first().username == "bob"
    assert actual[1].month == 2
    assert actual[1].price == 2


def test_income_summed_by_month(main_user, second_user):
    t1 = IncomeTypeFactory(title="AAA")
    t2 = IncomeTypeFactory(title="ZZZ")

    IncomePlanFactory(year=1999, month=1, price=1, income_type=t1)
    IncomePlanFactory(year=1999, month=2, price=2, income_type=t1)
    IncomePlanFactory(year=1999, month=2, price=2, income_type=t2)
    IncomePlanFactory(year=1974, journal=second_user.journal)

    actual = list(IncomePlanModelService(main_user).summed_by_month(1999))

    assert actual == [{"month": 1, "amount": 1}, {"month": 2, "amount": 4}]


@pytest.mark.parametrize("service, factory, type_factory, field, titles", TYPED_KINDS)
def test_typed_plan_items(
    main_user, second_user, service, factory, type_factory, field, titles
):
    for title in titles:
        factory(**{field: type_factory(title=title)})

    factory(journal=second_user.journal)

    actual = service(main_user).items()

    assert [str(plan) for plan in actual] == [f"1999/{t}" for t in sorted(titles)]
    assert actual[0].journal.users.first().username == "bob"
    assert actual[1].journal.users.first().username == "bob"


@pytest.mark.parametrize("service, factory, type_factory, field, titles", TYPED_KINDS)
def test_typed_plan_pivot_table(
    main_user, service, factory, type_factory, field, titles
):
    first = type_factory(title=titles[0])
    second = type_factory(title=titles[1])

    factory(month=1, price=1, **{field: first})
    factory(month=2, price=2, **{field: first})
    factory(month=12, price=5, **{field: second})
    factory(year=2027, month=1, price=9, **{field: first})

    actual = service(main_user).pivot_table(year=1999)

    assert actual == {second: {12: 5}, first: {1: 1, 2: 2}}


@pytest.mark.parametrize("service", SERVICES)
def test_plan_pivot_table_no_data(main_user, service):
    actual = service(main_user).pivot_table(year=1999)

    assert actual == {}


@pytest.mark.parametrize("kind", PLAN_KINDS, ids=lambda k: k.model.__name__)
def test_plan_row_cannot_be_stored_twice(kind):
    first = kind.factory()
    same = {
        field: getattr(first, field)
        for field in ("journal", "year", "month", "price", *kind.grouping)
    }

    with pytest.raises(IntegrityError), transaction.atomic():
        kind.factory(**same)


def test_expense_everyday_by_month(main_user, second_user):
    t1 = ExpenseTypeFactory(title="AAA")
    t2 = ExpenseTypeFactory(title="ZZZ")
    t3 = ExpenseTypeFactory(title="XXX", necessary=True)

    ExpensePlanFactory(year=1999, month=1, price=1, expense_type=t1)
    ExpensePlanFactory(year=1999, month=2, price=2, expense_type=t1)
    ExpensePlanFactory(year=1999, month=2, price=2, expense_type=t2)
    ExpensePlanFactory(year=1999, month=2, price=4, expense_type=t3)
    ExpensePlanFactory(year=1974, journal=second_user.journal)

    actual = list(ExpensePlanModelService(main_user).everyday_by_month(1999))

    assert actual == [{"month": 1, "amount": 1}, {"month": 2, "amount": 4}]


def test_expense_necessary_by_month(main_user, second_user):
    t1 = ExpenseTypeFactory(title="AAA", necessary=True)
    t2 = ExpenseTypeFactory(title="ZZZ", necessary=True)
    t3 = ExpenseTypeFactory(title="XXX")

    ExpensePlanFactory(year=1999, month=1, price=1, expense_type=t1)
    ExpensePlanFactory(year=1999, month=2, price=2, expense_type=t1)
    ExpensePlanFactory(year=1999, month=2, price=2, expense_type=t2)
    ExpensePlanFactory(year=1999, month=2, price=4, expense_type=t3)
    ExpensePlanFactory(year=1974, journal=second_user.journal)

    actual = list(ExpensePlanModelService(main_user).necessary_by_month(1999))

    assert actual == [{"month": 1, "amount": 1}, {"month": 2, "amount": 4}]


def test_expense_summed_by_month_sums_every_plan(main_user, second_user):
    ExpensePlanFactory(
        year=1999, month=2, price=2, expense_type=ExpenseTypeFactory(title="AAA")
    )
    ExpensePlanFactory(
        year=1999,
        month=2,
        price=4,
        expense_type=ExpenseTypeFactory(title="XXX", necessary=True),
    )
    ExpensePlanFactory(year=1974, journal=second_user.journal)

    actual = list(ExpensePlanModelService(main_user).summed_by_month(1999))

    assert actual == [{"month": 2, "amount": 6}]


@pytest.mark.parametrize(
    "read",
    [
        pytest.param(lambda service: service.year(1999), id="year"),
        pytest.param(lambda service: service.items(), id="items"),
    ],
)
def test_expense_read_query_count(main_user, django_assert_max_num_queries, read):
    with django_assert_max_num_queries(1):
        list(read(ExpensePlanModelService(main_user)))


def test_saving_summed_by_month(main_user, second_user):
    t1 = SavingTypeFactory(title="AAA")
    t2 = SavingTypeFactory(title="ZZZ")

    SavingPlanFactory(year=1999, month=1, price=1, saving_type=t1)
    SavingPlanFactory(year=1999, month=2, price=2, saving_type=t1)
    SavingPlanFactory(year=1999, month=2, price=2, saving_type=t2)
    SavingPlanFactory(year=1974, journal=second_user.journal)

    actual = list(SavingPlanModelService(main_user).summed_by_month(1999))

    assert actual == [{"month": 1, "amount": 1}, {"month": 2, "amount": 4}]


@pytest.mark.parametrize(
    "plans, expect",
    [
        pytest.param([(2, 22)], [{"month": 2, "amount": 22}], id="one_month"),
        pytest.param(
            [(1, 11), (2, 22)],
            [{"month": 1, "amount": 11}, {"month": 2, "amount": 22}],
            id="one_row_per_month",
        ),
    ],
)
def test_day_summed_by_month(main_user, plans, expect):
    for month, price in plans:
        DayPlanFactory(month=month, price=price)

    actual = list(DayPlanModelService(main_user).summed_by_month(1999))

    assert actual == expect


@pytest.mark.parametrize(
    "service, factory, attrs",
    [
        pytest.param(DayPlanModelService, DayPlanFactory, {}, id="day"),
        pytest.param(
            NecessaryPlanModelService,
            NecessaryPlanFactory,
            {"title": "other"},
            id="necessary",
        ),
    ],
)
def test_untyped_plan_items_by_year(main_user, second_user, service, factory, attrs):
    factory()
    factory(year=1974)
    factory(year=1974, journal=second_user.journal)

    actual = service(main_user).items()

    assert len(actual) == 2
    assert actual[0].journal.users.first().username == "bob"
    assert actual[0].year == 1974
    assert actual[1].journal.users.first().username == "bob"
    assert actual[1].year == 1999
    for plan in actual:
        for name, value in attrs.items():
            assert getattr(plan, name) == value


def test_day_pivot_table(main_user):
    DayPlanFactory(month=2, price=22)
    DayPlanFactory(month=12, price=222)

    actual = DayPlanModelService(main_user).pivot_table(1999)

    assert actual == {_("Daily"): {2: 22, 12: 222}}


@pytest.mark.parametrize(
    "title",
    [
        "Car Insurance",
        "Plan-A",
        "Test_123",
        "Lietuviškas įrašas",
    ],
)
def test_necessary_plan_title_valid(title):
    obj = NecessaryPlanFactory(title=title)
    obj.full_clean()


@pytest.mark.parametrize(
    "title",
    [
        pytest.param("ab", id="too_short"),
        pytest.param("a" * 101, id="too_long"),
        pytest.param("Drop * table", id="asterisk"),
        pytest.param("My@Plan", id="at_sign"),
        pytest.param("<script>alert('x')</script>", id="script_tag"),
        pytest.param("Hello!", id="exclamation"),
    ],
)
def test_necessary_plan_title_invalid(title):
    obj = NecessaryPlanFactory(title=title)

    with pytest.raises(ValidationError) as exc:
        obj.full_clean()

    assert "title" in exc.value.message_dict


def test_necessary_summed_by_month(main_user):
    t1 = ExpenseTypeFactory(title="AAA")
    t2 = ExpenseTypeFactory(title="XXX")
    NecessaryPlanFactory(expense_type=t1, title="A", month=2, price=123)
    NecessaryPlanFactory(expense_type=t2, title="A", month=2, price=321)

    actual = list(NecessaryPlanModelService(main_user).summed_by_month(1999))

    assert actual == [{"month": 2, "amount": 444}]


def test_necessary_summed_by_month_no_data(main_user):
    actual = list(NecessaryPlanModelService(main_user).summed_by_month(1999))

    assert not actual


@pytest.mark.parametrize(
    "service, table",
    [
        (IncomePlanModelService, "incomes_incometype"),
        (SavingPlanModelService, "savings_savingtype"),
        (NecessaryPlanModelService, "expenses_expensetype"),
    ],
)
def test_summed_by_month_joins_no_type_table(main_user, service, table):
    sql = str(service(main_user).summed_by_month(1999).query)

    assert table not in sql


@pytest.mark.parametrize(
    "method",
    [
        ExpensePlanModelService.everyday_by_month,
        ExpensePlanModelService.necessary_by_month,
    ],
)
def test_expense_by_month_joins_the_type_it_filters_on(main_user, method):
    sql = str(method(ExpensePlanModelService(main_user), 1999).query)

    assert "expenses_expensetype" in sql


def test_day_summed_by_month_joins_nothing(main_user):
    sql = str(DayPlanModelService(main_user).summed_by_month(1999).query)

    assert "JOIN" not in sql


@pytest.mark.parametrize("service", SERVICES)
def test_plans_do_not_join_the_journal(main_user, service):
    sql = str(service(main_user).items().query)

    assert "journals_journal" not in sql


@pytest.mark.parametrize(
    "service, table",
    [
        (IncomePlanModelService, "incomes_incometype"),
        (ExpensePlanModelService, "expenses_expensetype"),
        (SavingPlanModelService, "savings_savingtype"),
        (NecessaryPlanModelService, "expenses_expensetype"),
    ],
)
def test_plans_select_their_type(main_user, service, table):
    sql = str(service(main_user).items().query)

    assert table in sql


def test_necessary_same_title(main_user):
    NecessaryPlanFactory(
        year=2000, title="A", expense_type=ExpenseTypeFactory(title="X")
    )
    NecessaryPlanFactory(
        year=2000, title="A", expense_type=ExpenseTypeFactory(title="Y")
    )

    actual = NecessaryPlanModelService(main_user).items()

    assert len(actual) == 2

    assert actual[0].title == "A"
    assert actual[0].expense_type.title == "X"

    assert actual[1].title == "A"
    assert actual[1].expense_type.title == "Y"


def test_necessary_pivot_table(main_user):
    car = ExpenseTypeFactory(title="Car")
    NecessaryPlanFactory(expense_type=car, title="Insurance", month=2, price=123)

    actual = NecessaryPlanModelService(main_user).pivot_table(1999)

    assert actual == {(car, "Insurance"): {2: 123}}


@pytest.mark.parametrize("kind", PLAN_KINDS, ids=lambda k: k.model.__name__)
@pytest.mark.parametrize("column", ["price", "month"])
def test_plan_row_cannot_store_null(kind, column):
    with pytest.raises(IntegrityError), transaction.atomic():
        kind.factory(**{column: None})
