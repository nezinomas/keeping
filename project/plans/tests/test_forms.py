from datetime import date

import pytest
from django.db import IntegrityError
from django.db.models import QuerySet
from django.utils.translation import gettext as _

from ...core.tests.utils import count_queries
from ..forms import (
    CopyPlanForm,
    IncomePlanForm,
    NecessaryPlanForm,
)
from ..services.model_services import IncomePlanModelService
from ..tests.factories import (
    PLAN_KINDS,
    DayPlan,
    ExpensePlan,
    ExpensePlanFactory,
    ExpenseTypeFactory,
    IncomePlan,
    IncomePlanFactory,
    IncomeTypeFactory,
    NecessaryPlan,
    SavingPlan,
)

pytestmark = pytest.mark.django_db

TODAY = date(1999, 1, 1)

MONTHS = [
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
]


BLANK_DATA_ERRORS = {
    IncomePlan: {"year", "income_type"},
    ExpensePlan: {"year", "expense_type"},
    SavingPlan: {"year", "saving_type"},
    NecessaryPlan: {"year", "expense_type", "title"},
    DayPlan: {"year"},
}

DUPLICATE_MESSAGES = {
    IncomePlan: "1999 metai su 'Mine'  jau turi tikslą.",
    ExpensePlan: "1999 metai su 'Mine'  jau turi tikslą.",
    SavingPlan: "1999 metai su 'Mine'  jau turi tikslą.",
    NecessaryPlan: "1999 metai su 'Mine ir Rent'  jau turi tikslą.",
    DayPlan: "1999 metai jau turi tikslą.",
}

GROUPED_KINDS = [kind for kind in PLAN_KINDS if kind.grouping]


@pytest.mark.parametrize("kind", PLAN_KINDS, ids=lambda k: k.model.__name__)
def test_plan_blank_data(main_user, kind):
    form = kind.form(user=main_user, today=TODAY, data={})

    assert not form.is_valid()
    assert set(form.errors) == BLANK_DATA_ERRORS[kind.model]


@pytest.mark.parametrize("kind", PLAN_KINDS, ids=lambda k: k.model.__name__)
def test_plan_negative_number(main_user, kind):
    types = {f: t.pk for f, t in _owned_types(kind, main_user.journal).items()}
    data = {"year": 1999, **kind.extra, **types, **{m: -1.00 for m in MONTHS}}

    form = kind.form(user=main_user, today=TODAY, data=data)

    assert not form.is_valid()
    assert len(form.errors) == 12


@pytest.mark.parametrize("kind", PLAN_KINDS, ids=lambda k: k.model.__name__)
def test_plan_duplicate_is_refused(main_user, kind):
    types = _owned_types(kind, main_user.journal)
    kind.factory(year=1999, journal=main_user.journal, **kind.extra, **types)
    pks = {f: t.pk for f, t in types.items()}

    form = kind.form(
        user=main_user,
        today=TODAY,
        data={"year": 1999, **kind.extra, **pks, "january": 666.00},
    )

    assert not form.is_valid()
    assert form.errors["__all__"] == [DUPLICATE_MESSAGES[kind.model]]


@pytest.mark.parametrize("kind", GROUPED_KINDS, ids=lambda k: k.model.__name__)
def test_plan_another_grouping_is_not_a_duplicate(main_user, kind):
    first = _owned_types(kind, main_user.journal, title="First")
    kind.factory(year=1999, journal=main_user.journal, **kind.extra, **first)
    second = _owned_types(kind, main_user.journal, title="Second")
    pks = {f: t.pk for f, t in second.items()}

    form = kind.form(
        user=main_user,
        today=TODAY,
        data={"year": 1999, **kind.extra, **pks, "january": 15.00},
    )

    assert form.is_valid()


@pytest.mark.parametrize("kind", PLAN_KINDS, ids=lambda k: k.model.__name__)
def test_plan_save_converts_to_cents(main_user, kind):
    types = _owned_types(kind, main_user.journal)
    pks = {f: t.pk for f, t in types.items()}
    form = kind.form(
        data={"year": 1999, **kind.extra, **pks, "january": 0.01, "march": 2.5},
        user=main_user,
        today=TODAY,
    )

    assert form.is_valid()
    form.save()

    assert kind.model.objects.count() == 2

    jan_plan = kind.model.objects.get(month=1)
    mar_plan = kind.model.objects.get(month=3)

    assert jan_plan.price == 1
    assert mar_plan.price == 250
    for plan in (jan_plan, mar_plan):
        assert plan.year == 1999
        for field, value in {**kind.extra, **types}.items():
            assert getattr(plan, field) == value


def test_income_month_accepts_a_decimal_comma(main_user):
    income_type = IncomeTypeFactory()

    form = IncomePlanForm(
        data={"year": 1999, "income_type": income_type.pk, "january": "12,1"},
        user=main_user,
        today=TODAY,
    )

    assert form.is_valid(), form.errors
    form.save()

    assert IncomePlan.objects.get(month=1).price == 1210


@pytest.mark.parametrize("kind", PLAN_KINDS, ids=lambda k: k.model.__name__)
def test_plan_loads_initial_and_converts_from_cents(main_user, kind):
    types = _owned_types(kind, main_user.journal)
    grouping = {**kind.extra, **types}
    plan_jan = kind.factory(
        year=1999, month=1, price=15_000, journal=main_user.journal, **grouping
    )
    kind.factory(
        year=1999, month=12, price=30_000, journal=main_user.journal, **grouping
    )

    form = kind.form(instance=plan_jan, user=main_user, today=TODAY)

    assert form.initial["year"] == 1999
    for field, value in kind.extra.items():
        assert form.initial[field] == value
    for field, type_ in types.items():
        assert form.initial[field] == type_.pk

    assert float(form.initial["january"]) == 150.00
    assert float(form.initial["december"]) == 300.00
    assert "february" not in form.initial

    assert form.fields["year"].disabled is True
    for field in kind.grouping:
        assert form.fields[field].disabled is True


@pytest.mark.parametrize("kind", PLAN_KINDS, ids=lambda k: k.model.__name__)
def test_plan_updates_and_deletes_rows(main_user, kind):
    types = _owned_types(kind, main_user.journal)
    grouping = {**kind.extra, **types}
    plan_jan = kind.model.objects.create(
        year=2026, month=1, price=10000, journal=main_user.journal, **grouping
    )
    kind.model.objects.create(
        year=2026, month=2, price=20000, journal=main_user.journal, **grouping
    )
    pks = {f: t.pk for f, t in types.items()}

    form = kind.form(
        data={
            "year": 2026,
            **kind.extra,
            **pks,
            "january": 150.00,
            "february": "",
            "march": 300.00,
        },
        instance=plan_jan,
        user=main_user,
        today=TODAY,
    )
    assert form.is_valid()
    form.save()

    assert kind.model.objects.count() == 2
    assert kind.model.objects.filter(month=2).exists() is False
    assert kind.model.objects.get(month=1).price == 15000
    assert kind.model.objects.get(month=3).price == 30000


@pytest.mark.parametrize("kind", GROUPED_KINDS, ids=lambda k: k.model.__name__)
def test_plan_form_prevents_cross_category_pollution(main_user, kind):
    mine = _owned_types(kind, main_user.journal, title="Salary")
    noise = _owned_types(kind, main_user.journal, title="Gift")
    instance = kind.factory(
        year=2026,
        month=1,
        price=100000,
        journal=main_user.journal,
        **kind.extra,
        **mine,
    )
    kind.factory(
        year=2026,
        month=2,
        price=50000,
        journal=main_user.journal,
        **kind.extra,
        **noise,
    )

    form = kind.form(user=main_user, today=TODAY, instance=instance)

    assert form.initial["january"] == 1000.0
    assert "february" not in form.initial, "Cross-category pollution detected!"


def test_necessary_form_title_valid(
    main_user,
):
    expense_type = ExpenseTypeFactory()

    data = {
        "title": "Car Insurance-2026_A",
        "expense_type": expense_type.pk,
        "january": 100.50,
        "year": 1999,
    }

    form = NecessaryPlanForm(data=data, user=main_user, today=TODAY)

    assert form.is_valid(), f"Form should be valid, but got errors: {form.errors}"


def test_necessary_form_title_too_short(main_user):
    expense_type = ExpenseTypeFactory()

    data = {
        "title": "ab",
        "expense_type": expense_type.pk,
        "year": 1999,
        "january": 100.50,
    }

    form = NecessaryPlanForm(data=data, user=main_user, today=TODAY)

    assert not form.is_valid()
    assert "title" in form.errors

    assert (
        "Įsitikinkite, kad reikšmė sudaryta iš nemažiau kaip 3 ženklų (dabartinis ilgis 2)."
        in form.errors["title"][0]
    )


def test_necessary_form_title_too_long(main_user):
    expense_type = ExpenseTypeFactory()

    data = {
        "title": "a" * 101,
        "expense_type": expense_type.pk,
        "year": 1999,
        "january": 100.50,
    }

    form = NecessaryPlanForm(data=data, user=main_user, today=TODAY)

    assert not form.is_valid()
    assert "title" in form.errors
    assert (
        "Įsitikinkite, kad reikšmė sudaryta iš nedaugiau kaip 100 ženklų (dabartinis ilgis 101)."
        in form.errors["title"][0]
    )


@pytest.mark.parametrize(
    "title",
    [
        "Drop * table",
        "My@Plan",
        "<script>alert('x')</script>",
        "Insurance/Home",
    ],
)
def test_necessary_form_title_invalid_characters(main_user, title):
    expense_type = ExpenseTypeFactory()

    data = {
        "title": title,
        "expense_type": expense_type.pk,
        "year": 1999,
        "january": 100.50,
    }

    form = NecessaryPlanForm(data=data, user=main_user, today=TODAY)

    assert not form.is_valid()
    assert "title" in form.errors

    assert (
        _("Title can only contain letters, numbers, spaces, hyphens, and underscores.")
        in form.errors["title"][0]
    )


def test_copy_init(main_user):
    form = CopyPlanForm(user=main_user, today=TODAY)
    assert form.fields["year_from"].initial == 1999
    assert form.fields["year_to"].initial == 2000
    assert form.fields["income"].initial is True
    assert form.fields["expense"].initial is True
    assert form.fields["saving"].initial is True
    assert form.fields["day"].initial is True
    assert form.fields["necessary"].initial is True


def test_copy_have_fields(main_user):
    form = CopyPlanForm(user=main_user, today=TODAY).as_p()

    assert '<input type="text" name="year_from"' in form
    assert '<input type="text" name="year_to"' in form
    assert '<input type="checkbox" name="income"' in form
    assert '<input type="checkbox" name="expense"' in form
    assert '<input type="checkbox" name="saving"' in form
    assert '<input type="checkbox" name="day"' in form
    assert '<input type="checkbox" name="necessary"' in form


def test_copy_checkboxes_keep_their_order_and_labels(main_user):
    form = CopyPlanForm(user=main_user, today=TODAY)

    actual = [(name, str(field.label)) for name, field in form.fields.items()]

    assert actual[2:] == [
        ("income", "Pajamų planai"),
        ("expense", "Išlaidų planai"),
        ("saving", "Taupymo planai"),
        ("day", "Dienos planai"),
        ("necessary", "Papildomų būtinų išlaidų planus"),
    ]


def test_copy_blank_data(main_user):
    form = CopyPlanForm(user=main_user, today=TODAY, data={})

    assert not form.is_valid()
    assert form.errors == {
        "year_from": ["Šis laukas yra privalomas."],
        "year_to": ["Šis laukas yra privalomas."],
    }


def test_copy_all_checkboxes_unselected(main_user):
    form = CopyPlanForm(
        user=main_user,
        today=TODAY,
        data={
            "year_from": 1999,
            "year_to": 2000,
        },
    )

    assert not form.is_valid()
    assert form.errors == {"__all__": ["Reikia pažymėti nors vieną planą."]}


def test_copy_empty_from_tables(main_user):
    form = CopyPlanForm(
        user=main_user,
        today=TODAY,
        data={"year_from": 1999, "year_to": 2000, "income": True},
    )

    assert not form.is_valid()
    assert form.errors == {"income": ["Nėra ką kopijuoti."]}


def test_copy_to_table_have_records(main_user):
    IncomePlanFactory(year=1999, journal=main_user.journal)
    IncomePlanFactory(year=2000, journal=main_user.journal)

    form = CopyPlanForm(
        user=main_user,
        today=TODAY,
        data={"year_from": 1999, "year_to": 2000, "income": True},
    )

    assert not form.is_valid()
    assert form.errors == {"income": ["2000 metai jau turi planus."]}


def test_copy_to_table_have_records_from_empty(main_user):
    IncomePlanFactory(year=2000, journal=main_user.journal)

    form = CopyPlanForm(
        user=main_user,
        today=TODAY,
        data={"year_from": 1999, "year_to": 2000, "income": True},
    )

    assert not form.is_valid()
    assert form.errors == {
        "income": ["Nėra ką kopijuoti.", "2000 metai jau turi planus."]
    }


def test_copy_data(main_user):
    income_type = IncomeTypeFactory(journal=main_user.journal)

    IncomePlanFactory(
        year=1999,
        month=1,
        price=100,
        income_type=income_type,
        journal=main_user.journal,
    )
    IncomePlanFactory(
        year=1999,
        month=3,
        price=300,
        income_type=income_type,
        journal=main_user.journal,
    )

    form = CopyPlanForm(
        user=main_user,
        today=TODAY,
        data={"year_from": 1999, "year_to": 2000, "income": True},
    )

    assert form.is_valid()
    form.save()

    copied_data = IncomePlanModelService(main_user).year(2000)

    assert copied_data.count() == 2
    assert copied_data.get(month=1).price == 100
    assert copied_data.get(month=3).price == 300
    assert {row.journal for row in copied_data} == {main_user.journal}
    assert {row.income_type for row in copied_data} == {income_type}


COPY_CHECKBOX = {
    IncomePlan: "income",
    ExpensePlan: "expense",
    SavingPlan: "saving",
    DayPlan: "day",
    NecessaryPlan: "necessary",
}


def _copy_queries(user, kind, year_from, months):
    first = kind.factory(journal=user.journal, year=year_from, month=1, price=100)
    copied = {f: getattr(first, f) for f in kind.grouping}
    for month in range(2, months + 1):
        kind.factory(
            journal=user.journal,
            year=year_from,
            month=month,
            price=month * 100,
            **copied,
        )
    form = CopyPlanForm(
        user=user,
        today=TODAY,
        data={
            "year_from": year_from,
            "year_to": year_from + 1,
            COPY_CHECKBOX[kind.model]: True,
        },
    )
    assert form.is_valid(), form.errors
    return count_queries(form.save)


def test_copy_a_failing_kind_leaves_no_kind_copied(main_user, mocker):
    IncomePlanFactory(journal=main_user.journal, year=1999, month=1)
    ExpensePlanFactory(journal=main_user.journal, year=1999, month=1)
    form = CopyPlanForm(
        user=main_user,
        today=TODAY,
        data={"year_from": 1999, "year_to": 2000, "income": True, "expense": True},
    )
    assert form.is_valid(), form.errors

    real = QuerySet.bulk_create

    def fail_on_expenses(qs, objs, *args, **kwargs):
        if qs.model is ExpensePlan:
            raise IntegrityError
        return real(qs, objs, *args, **kwargs)

    mocker.patch.object(QuerySet, "bulk_create", fail_on_expenses)

    with pytest.raises(IntegrityError):
        form.save()

    assert not IncomePlan.objects.filter(year=2000).exists()


@pytest.mark.parametrize("kind", PLAN_KINDS, ids=lambda k: k.model.__name__)
def test_copy_query_count_does_not_grow_with_the_rows(main_user, kind):
    few = _copy_queries(main_user, kind, 2001, 2)
    many = _copy_queries(main_user, kind, 2003, 6)

    assert many == few
    assert kind.model.objects.filter(year=2004).count() == 6


# A posted journal never moves a plan to another journal
def _owned_types(kind, journal, title="Mine"):
    return {
        field: type_factory(title=title, journal=journal)
        for field, type_factory in kind.type_factories.items()
    }


def _plan_data(kind, main_user, second_user):
    types = {f: t.pk for f, t in _owned_types(kind, main_user.journal).items()}
    return {
        "journal": second_user.journal.pk,
        "year": 1999,
        "january": 1.5,
        **kind.extra,
        **types,
    }


@pytest.mark.parametrize("kind", PLAN_KINDS, ids=lambda k: k.model.__name__)
def test_plan_form_renders_no_user_select(main_user, kind):
    rendered_html = kind.form(user=main_user, today=TODAY).as_p()

    assert 'name="user"' not in rendered_html


@pytest.mark.parametrize("month", MONTHS)
@pytest.mark.parametrize("kind", PLAN_KINDS, ids=lambda k: k.model.__name__)
def test_plan_form_fields(main_user, kind, month):
    form = kind.form(user=main_user, today=TODAY)

    assert month in form.fields
    assert "journal" not in form.fields


@pytest.mark.parametrize("kind", PLAN_KINDS, ids=lambda k: k.model.__name__)
def test_plan_year_starts_at_the_users_year(main_user, kind):
    form = kind.form(user=main_user, today=date(1974, 1, 1))

    assert form.fields["year"].initial == 1999


@pytest.mark.parametrize("kind", PLAN_KINDS, ids=lambda k: k.model.__name__)
def test_plan_create_ignores_a_posted_journal(main_user, second_user, kind):
    data = _plan_data(kind, main_user, second_user)

    form = kind.form(user=main_user, today=TODAY, data=data)

    assert form.is_valid()

    form.save()

    assert kind.model.objects.count() == 1
    assert kind.model.objects.get().journal == main_user.journal


@pytest.mark.parametrize("kind", PLAN_KINDS, ids=lambda k: k.model.__name__)
def test_plan_edit_ignores_a_posted_journal(main_user, second_user, kind):
    data = _plan_data(kind, main_user, second_user)

    obj = kind.factory(
        journal=main_user.journal,
        **kind.extra,
        **_owned_types(kind, main_user.journal),
    )

    form = kind.form(user=main_user, today=TODAY, instance=obj, data=data)

    assert form.is_valid()

    form.save()

    assert set(kind.model.objects.values_list("journal", flat=True)) == {
        main_user.journal.pk
    }


@pytest.fixture(params=PLAN_KINDS, ids=lambda k: k.model.__name__)
def zero_month_plan(request, main_user):
    kind = request.param
    jan = kind.factory(journal=main_user.journal, month=1, price=15_000)
    copied = {f: getattr(jan, f) for f in kind.grouping}
    kind.factory(journal=main_user.journal, month=2, price=0, **copied)
    return kind, jan


def test_edit_shows_a_stored_zero_month_as_empty_field(main_user, zero_month_plan):
    kind, jan = zero_month_plan

    form = kind.form(instance=jan, user=main_user, today=TODAY)

    assert "value=" not in str(form["february"])
    assert 'value="150.0"' in str(form["january"])


def test_resave_with_the_zero_month_still_empty_deletes_its_row(
    main_user, zero_month_plan
):
    kind, jan = zero_month_plan
    grouping = {f: jan.serializable_value(f) for f in kind.grouping}
    data = {"year": 1999, **grouping, "january": 150.00, "february": ""}

    form = kind.form(data=data, instance=jan, user=main_user, today=TODAY)
    assert form.is_valid(), form.errors
    form.save()

    assert kind.model.objects.filter(month=2).exists() is False
    assert kind.model.objects.get(month=1).price == 15_000


def _months(year, months):
    return {"year": year, **{m: 2.5 for m in MONTHS[:months]}}


def _free_grouping(main_user, kind, year):
    owner = kind.factory(journal=main_user.journal, year=year - 1000)
    grouping = _grouping_of(kind, owner)
    owner.delete()
    return grouping


def _grouping_of(kind, instance):
    return {f: instance.serializable_value(f) for f in kind.grouping}


def _save_query_count(main_user, kind, data, **form_kwargs):
    form = kind.form(user=main_user, today=TODAY, data=data, **form_kwargs)
    assert form.is_valid(), form.errors

    return count_queries(form.save)


@pytest.mark.parametrize("kind", PLAN_KINDS, ids=lambda k: k.model.__name__)
def test_save_create_query_count_does_not_grow_with_months(main_user, kind):
    def count(year, months):
        data = {**_months(year, months), **_free_grouping(main_user, kind, year)}
        return _save_query_count(main_user, kind, data)

    few = count(2001, 2)
    many = count(2002, 12)

    assert many == few


@pytest.mark.parametrize("kind", PLAN_KINDS, ids=lambda k: k.model.__name__)
def test_save_update_query_count_does_not_grow_with_months(main_user, kind):
    def stored(year, months):
        first = kind.factory(journal=main_user.journal, year=year, month=1)
        copied = {f: getattr(first, f) for f in kind.grouping}
        for month in range(2, months + 1):
            kind.factory(journal=main_user.journal, year=year, month=month, **copied)
        return first

    def count(year, months):
        instance = stored(year, months)
        data = {**_months(year, months), **_grouping_of(kind, instance)}
        return _save_query_count(main_user, kind, data, instance=instance)

    few = count(2001, 2)
    many = count(2002, 12)

    assert many == few
