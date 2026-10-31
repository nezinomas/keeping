import pytest

from ...services.model_services import AccountModelService


def test_account_model_service_promises_no_year():
    assert not hasattr(AccountModelService, "year")


@pytest.mark.django_db
def test_a_user_with_no_year_raises(main_user):
    main_user.year = None

    with pytest.raises(ValueError, match="has no year"):
        AccountModelService(main_user).items()
