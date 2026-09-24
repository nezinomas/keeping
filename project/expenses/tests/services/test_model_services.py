import re
from datetime import date

import pytest
from django.contrib.auth.models import AnonymousUser
from mock import MagicMock

from ... import models
from ...services.model_services import (
    ExpenseKeywordModelService,
    ExpenseModelService,
    ExpenseNameModelService,
    ExpenseTypeModelService,
)
from .. import factories


def test_expense_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        ExpenseModelService(user=None)


def test_expense_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        ExpenseModelService(user=anon)


@pytest.mark.django_db
def test_expense_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    ExpenseModelService(user=main_user)


def test_expense_type_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        ExpenseTypeModelService(user=None)


def test_expense_type_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        ExpenseTypeModelService(user=anon)


@pytest.mark.django_db
def test_expense_type_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    ExpenseTypeModelService(user=main_user)


def test_expense_name_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        ExpenseNameModelService(user=None)


def test_expense_name_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        ExpenseNameModelService(user=anon)


@pytest.mark.django_db
def test_expense_name_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    ExpenseNameModelService(user=main_user)


@pytest.mark.django_db
class TestExpenseService:
    @pytest.fixture
    def service(self, main_user):
        return ExpenseModelService(main_user)

    def test_expenses_list_structure_and_values(self, service):
        """
        It should return a dictionary with correct keys and formatted values.
        """
        # Arrange
        obj = factories.ExpenseFactory(
            price=120050,  # 1200.50 (stored as int)
            attachment="receipt.pdf",
            remark="Test Remark",
            quantity=10,
            exception=True,
        )
        qs = models.Expense.objects.all()

        # Act
        results = service.expenses_list(qs)
        result = results[0]

        # Assert 1: Check all required dictionary keys exist
        expected_keys = {
            "id",
            "date",
            "account__title",
            "expense_type__pk",
            "expense_type__title",
            "expense_name__title",
            "quantity",
            "remark",
            "attachment",
            "exception",
            "price_str",
            "is_pdf",
            "month_group",
        }
        assert expected_keys.issubset(result.keys())

        # Assert 2: Check Values
        assert result["id"] == obj.pk
        assert result["remark"] == "Test Remark"
        assert result["quantity"] == 10
        assert result["exception"] is True

        # Assert 3: Check PDF Logic
        assert result["is_pdf"] is True

        # Assert 4: Check Price Formatting (Enabled via fixture)
        # 120050 / 100 = 1200.50 -> Locale lt_LT -> "1.200,50"
        assert result["price_str"] == "1.200,50"

    def test_expenses_list_urls(self, service):
        """
        It should generate correct update and delete URLs using the ID.
        """
        obj = factories.ExpenseFactory()
        qs = models.Expense.objects.all()

        result = service.expenses_list(qs)[0]

    def test_expenses_list_pdf_detection_vs_image(self, service):
        """
        It should correctly flag PDF files (True) vs images (False).
        """
        factories.ExpenseFactory(attachment="contract.pdf", price=100)
        factories.ExpenseFactory(attachment="photo.jpg", price=100)

        qs = models.Expense.objects.order_by("id")

        results = list(service.expenses_list(qs))

        assert results[0]["is_pdf"] is False  # JPG
        assert results[1]["is_pdf"] is True  # PDF

    def test_expenses_list_ordering(self, service):
        """
        It should order by Date DESC, then ExpenseType, then ExpenseName ASC.
        """

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

        results = list(service.expenses_list(qs))

        assert results[0]["id"] == e3.pk
        assert results[1]["id"] == e2.pk
        assert results[2]["id"] == e1.pk

    def test_expenses_list_empty_queryset(self, service):
        """
        It should return an empty list if queryset is empty, without crashing.
        """
        qs = models.Expense.objects.none()
        results = service.expenses_list(qs)
        assert not list(results)


def test_expense_keyword_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        ExpenseKeywordModelService(user=None)


def test_expense_keyword_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        ExpenseKeywordModelService(user=anon)


@pytest.mark.django_db
def test_expense_keyword_init_succeeds_with_real_user(main_user):
    ExpenseKeywordModelService(user=main_user)


@pytest.mark.django_db
def test_expense_keyword_items(main_user):
    factories.ExpenseKeywordFactory(journal=main_user.journal, keyword="jogurt")
    factories.ExpenseKeywordFactory(journal=main_user.journal, keyword="banan")

    actual = ExpenseKeywordModelService(main_user).items()

    assert actual.count() == 2


@pytest.mark.django_db
def test_expense_keyword_items_other_journal(main_user, second_user):
    other_name = factories.ExpenseNameFactory(
        parent=factories.ExpenseTypeFactory(
            title="Buitinės", journal=second_user.journal
        )
    )
    factories.ExpenseKeywordFactory(journal=main_user.journal, keyword="jogurt")
    factories.ExpenseKeywordFactory(
        journal=second_user.journal, keyword="banan", expense_name=other_name
    )

    actual = ExpenseKeywordModelService(main_user).items()

    assert actual.count() == 1
    assert actual[0].keyword == "jogurt"


@pytest.mark.django_db
def test_expense_keyword_year(main_user):
    name_2024 = factories.ExpenseNameFactory(
        title="N2024",
        parent=factories.ExpenseTypeFactory(journal=main_user.journal),
        valid_for=2024,
    )
    name_2026 = factories.ExpenseNameFactory(
        title="N2026", parent=factories.ExpenseTypeFactory(journal=main_user.journal)
    )
    factories.ExpenseKeywordFactory(
        journal=main_user.journal, keyword="old", expense_name=name_2024
    )
    factories.ExpenseKeywordFactory(
        journal=main_user.journal, keyword="new", expense_name=name_2026
    )

    actual = ExpenseKeywordModelService(main_user).year(2026)

    assert actual.count() == 1
    assert actual[0].keyword == "new"


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


def test_year_method_raises_not_implemented_error(mocker):
    mocker.patch(
        "project.expenses.services.model_services.ExpenseTypeModelService.get_queryset",
        return_value="X",
    )
    service = ExpenseTypeModelService(user=MagicMock())

    expected_msg = (
        "ExpenseTypeModelService.year is not implemented. Use items() instead."
    )
    with pytest.raises(NotImplementedError, match=re.escape(expected_msg)):
        service.year(2023)


def test_year_method_does_not_call_database_pure_pytest(mocker):
    mock_qs = mocker.MagicMock()
    mocker.patch(
        "project.expenses.services.model_services.ExpenseTypeModelService.get_queryset",
        return_value=mock_qs,
    )

    service = ExpenseTypeModelService(mocker.MagicMock())

    with pytest.raises(NotImplementedError):
        service.year(2023)

    mock_qs.filter.assert_not_called()
