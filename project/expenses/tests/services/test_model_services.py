from datetime import date

import pytest

from ... import models
from ...services.model_services import (
    ExpenseKeywordModelService,
    ExpenseModelService,
    ExpenseTypeModelService,
)
from .. import factories


@pytest.mark.django_db
class TestExpenseService:
    @pytest.fixture
    def service(self, main_user):
        return ExpenseModelService(main_user)

    def test_expenses_list_structure_and_values(self, service):
        obj = factories.ExpenseFactory(
            price=120050,
            attachment="receipt.pdf",
            remark="Test Remark",
            quantity=10,
            exception=True,
        )
        qs = models.Expense.objects.all()

        actual = list(service.expenses_list(qs))

        assert actual == [
            {
                "id": obj.pk,
                "date": date(1999, 1, 1),
                "account__title": "Account1",
                "expense_type__pk": obj.expense_type.pk,
                "expense_type__title": "Expense Type",
                "expense_name__title": "Expense Name",
                "quantity": 10,
                "remark": "Test Remark",
                "attachment": "receipt.pdf",
                "exception": True,
                "price_str": "1.200,50",
                "is_pdf": True,
                "month_group": date(1999, 1, 1),
            }
        ]

    def test_expenses_list_pdf_detection_vs_image(self, service):
        factories.ExpenseFactory(attachment="contract.pdf", price=100)
        factories.ExpenseFactory(attachment="photo.jpg", price=100)

        qs = models.Expense.objects.order_by("id")

        actual = service.expenses_list(qs)

        assert [a["is_pdf"] for a in actual] == [False, True]

    def test_expenses_list_ordering(self, service):
        e1 = factories.ExpenseFactory(
            date=date(2000, 1, 1), expense_name__title="Z_Name"
        )
        e2 = factories.ExpenseFactory(
            date=date(2025, 1, 1), expense_name__title="B_Name"
        )
        e3 = factories.ExpenseFactory(
            date=date(2025, 1, 1), expense_name__title="A_Name"
        )

        qs = models.Expense.objects.all()

        actual = service.expenses_list(qs)

        assert [a["id"] for a in actual] == [e3.pk, e2.pk, e1.pk]

    def test_expenses_list_empty_queryset(self, service):
        qs = models.Expense.objects.none()
        results = service.expenses_list(qs)
        assert not list(results)


@pytest.mark.django_db
def test_expense_keyword_items_other_journal(main_user, second_user):
    other_name = factories.ExpenseNameFactory(
        parent=factories.ExpenseTypeFactory(
            title="Buitinės", journal=second_user.journal
        )
    )
    factories.ExpenseKeywordFactory(journal=main_user.journal, keyword="jogurt")
    factories.ExpenseKeywordFactory(journal=main_user.journal, keyword="kefyr")
    factories.ExpenseKeywordFactory(
        journal=second_user.journal, keyword="banan", expense_name=other_name
    )

    actual = ExpenseKeywordModelService(main_user).items()

    assert sorted(a.keyword for a in actual) == ["jogurt", "kefyr"]


@pytest.mark.django_db
def test_expense_keyword_year_same_titled_names_in_other_types(main_user):
    maistas = factories.ExpenseTypeFactory(title="Maistas", journal=main_user.journal)
    buitines = factories.ExpenseTypeFactory(title="Buitinės", journal=main_user.journal)
    old_kita = factories.ExpenseNameFactory(
        title="Kita", parent=maistas, valid_for=2024
    )
    kita = factories.ExpenseNameFactory(title="Kita", parent=buitines)
    factories.ExpenseKeywordFactory(
        journal=main_user.journal, keyword="duon", expense_name=old_kita
    )
    factories.ExpenseKeywordFactory(
        journal=main_user.journal, keyword="servet", expense_name=kita
    )

    actual = ExpenseKeywordModelService(main_user).year(2026)

    assert [(k.keyword, k.expense_name.parent) for k in actual] == [
        ("servet", buitines)
    ]


def test_expense_type_model_service_promises_no_year():
    assert not hasattr(ExpenseTypeModelService, "year")
