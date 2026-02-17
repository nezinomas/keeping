import re
from datetime import date

import pytest
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from mock import MagicMock

from .. import factories
from ... import models
from ...services.model_services import (
    ExpenseModelService,
    ExpenseNameModelService,
    ExpenseTypeModelService,
)


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
            "url_update",
            "url_delete",
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

        # We expect the URL to match the standard Django reverse for this ID
        expected_update = reverse("expenses:update", args=[obj.pk])
        expected_delete = reverse("expenses:delete", args=[obj.pk])

        assert result["url_update"] == expected_update
        assert result["url_delete"] == expected_delete

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
