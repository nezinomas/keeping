import pytest
from django.db import connection
from django.forms.models import modelformset_factory
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from mock import Mock

from ....accounts.tests.factories import AccountFactory
from ....bookkeeping import views
from ....bookkeeping.models import AccountWorth
from ....bookkeeping.tests.factories import AccountWorthFactory
from ....pensions.tests.factories import PensionTypeFactory
from ....savings.tests.factories import SavingTypeFactory
from ...mixins.formset import BaseTypeFormSet, FormsetMixin
from ..utils import setup_view


def worth_view(rf, main_user, view_class=views.AccountsWorthNew):
    rf.user = main_user
    return setup_view(view_class(), rf)


def post_data(rows):
    data = {"form-TOTAL_FORMS": len(rows), "form-INITIAL_FORMS": 0}
    for number, row in enumerate(rows):
        data |= {f"form-{number}-{name}": value for name, value in row.items()}
    return data


def unchanged_date(view):
    return view.get_formset_class()()["date"].value().strftime("%Y-%m-%d")


def bound_formset(view, rows, can_delete=False):
    formset_class = modelformset_factory(
        view.model_class,
        form=view.get_formset_class(),
        formset=BaseTypeFormSet,
        can_delete=can_delete,
        extra=0,
    )
    return formset_class(post_data(rows))


def posted_view(rf, main_user, rows):
    request = rf.post("/", post_data(rows))
    request.user = main_user
    return setup_view(views.AccountsWorthNew(), request)


class DummyTypesService:
    def __init__(self, user):
        self.user = user

    def items(self):
        return ["Account1", "Account2"]


class OnePensionService(DummyTypesService):
    def items(self):
        return ["P1"]


class NoItemsService(DummyTypesService):
    def items(self):
        return []


class StubFormsetView(FormsetMixin):
    pass


@pytest.mark.parametrize(
    "category_service, fund_field, expect",
    [
        pytest.param(
            OnePensionService, "pension_type", [{"pension_type": "P1"}], id="one_item"
        ),
        pytest.param(NoItemsService, "account", [], id="no_items"),
        pytest.param(
            DummyTypesService,
            "account",
            [{"account": "Account1"}, {"account": "Account2"}],
            id="account",
        ),
        pytest.param(
            DummyTypesService,
            "saving_type",
            [{"saving_type": "Account1"}, {"saving_type": "Account2"}],
            id="saving_type",
        ),
    ],
)
def test_formset_initial_keys_each_item_by_the_service_models_fund_field(
    fake_request, category_service, fund_field, expect
):
    service_instance = Mock()
    service_instance.objects.model = Mock(fund_field=fund_field)

    view = setup_view(StubFormsetView(), fake_request)
    view.category_service_class = category_service
    view.service_class = Mock(return_value=service_instance)

    assert view.formset_initial() == expect


@pytest.mark.django_db
def test_lazy_properties_are_built_once_for_the_request_user(rf, main_user):
    view = worth_view(rf, main_user)

    assert view.service_instance is view.service_instance
    assert view.service_instance.user == main_user
    assert view.model_class is AccountWorth


@pytest.mark.django_db
def test_get_formset_for_get_request(rf, main_user):
    a1 = AccountFactory(title="A1")
    a2 = AccountFactory(title="A2")
    AccountWorthFactory(account=a1)
    view = worth_view(rf, main_user)

    actual = view.get_formset()

    assert not actual.is_bound
    assert actual.extra == 2
    assert [form.initial["account"] for form in actual.forms] == [a1, a2]


@pytest.mark.django_db
def test_get_formset_for_post_request(rf, main_user):
    a1 = AccountFactory(title="A1")
    AccountFactory(title="A2")
    view = worth_view(rf, main_user)
    data = post_data([{"date": "1999-9-9", "price": "5", "account": a1.pk}])

    actual = view.get_formset(data)

    assert actual.is_bound
    assert actual.extra == 0
    assert len(actual.forms) == 1
    assert actual.forms[0]["account"].value() == a1.pk
    assert "account" not in actual.forms[0].initial


@pytest.mark.django_db
def test_post_with_invalid_formset_returns_the_formset_with_its_errors(rf, main_user):
    view = posted_view(rf, main_user, [{"date": "x", "price": "x", "account": 0}])

    response = view.post(view.request)

    formset = response.context_data["formset"]
    assert not formset.is_valid()
    assert set(formset.errors[0]) == {"date", "price", "account"}
    assert not AccountWorth.objects.exists()


@pytest.mark.django_db
def test_post_skips_empty_prices_and_does_not_save(rf, main_user):
    a1 = AccountFactory(title="A1")
    a2 = AccountFactory(title="A2")
    view = posted_view(
        rf,
        main_user,
        [
            {"date": "1999-9-9", "price": "", "account": a1.pk},
            {"date": "1999-9-9", "account": a2.pk},
        ],
    )

    response = view.post(view.request)

    assert response.status_code == 204
    assert not AccountWorth.objects.exists()


@pytest.mark.django_db
def test_post_saves_only_the_rows_with_a_price(rf, main_user):
    a1 = AccountFactory(title="A1")
    a2 = AccountFactory(title="A2")
    view = posted_view(
        rf,
        main_user,
        [
            {"date": "1999-9-9", "price": "100", "account": a1.pk},
            {"date": "1999-9-9", "price": "", "account": a2.pk},
        ],
    )

    response = view.post(view.request)

    actual = AccountWorth.objects.get()
    assert (actual.account, actual.price) == (a1, 10000)
    assert actual.date.strftime("%Y-%m-%d") == "1999-09-09"
    assert response["HX-Trigger"] == '{"afterAccountWorthNew": {}}'


@pytest.mark.django_db
def test_post_syncs_the_balances_of_the_saved_rows_user(rf, main_user, mocker):
    a1 = AccountFactory(title="A1")
    view = posted_view(
        rf, main_user, [{"date": "1999-9-9", "price": "100", "account": a1.pk}]
    )
    mock_sync = mocker.patch.object(views.AccountsWorthNew, "balance_sync")

    view.post(view.request)

    mock_sync.assert_called_once_with(main_user)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "count", [pytest.param(2, id="two"), pytest.param(6, id="six")]
)
def test_post_writes_all_rows_in_one_insert(client_logged, count):
    accounts = [AccountFactory(title=f"A{i}") for i in range(count)]
    rows = [{"date": "1999-9-9", "price": "5", "account": a.pk} for a in accounts]

    with CaptureQueriesContext(connection) as queries:
        client_logged.post(reverse("bookkeeping:accounts_worth_new"), post_data(rows))

    table = AccountWorth._meta.db_table
    inserts = [q for q in queries if q["sql"].startswith(f'INSERT INTO "{table}"')]
    assert len(inserts) == 1
    assert AccountWorth.objects.count() == count


@pytest.mark.django_db
def test_modal_renders_the_formset_under_its_title_and_worth_css_class(client_logged):
    account = AccountFactory(title="A1")

    response = client_logged.get(reverse("bookkeeping:accounts_worth_new"))

    actual = response.content.decode("utf-8")
    assert "Sąskaitų vertė" in actual
    assert 'class="modal-body worth-form"' in actual
    assert f'<option value="{account.pk}" selected>A1</option>' in actual


@pytest.fixture
def isolated_formset(mocker):
    mocker.patch.object(BaseTypeFormSet, "__init__", return_value=None)
    formset = BaseTypeFormSet()

    formset.model = mocker.Mock()
    formset.model.__name__ = "MockModel"
    return formset


@pytest.mark.django_db
@pytest.mark.parametrize(
    "view_class, factory, fund_field",
    [
        pytest.param(views.AccountsWorthNew, AccountFactory, "account", id="account"),
        pytest.param(
            views.SavingsWorthNew, SavingTypeFactory, "saving_type", id="saving_type"
        ),
        pytest.param(
            views.PensionsWorthNew, PensionTypeFactory, "pension_type", id="pension"
        ),
    ],
)
def test_clean_tags_the_fund_field_the_model_names(
    rf, main_user, view_class, factory, fund_field
):
    fund = factory()
    view = worth_view(rf, main_user, view_class)
    row = {"date": "1999-9-9", "price": "5", fund_field: fund.pk}

    actual = bound_formset(view, [row, row])

    assert not actual.is_valid()
    assert [set(form.errors) for form in actual.forms] == [{fund_field}] * 2


def test_clean_without_a_fund_field_raises(mocker, isolated_formset):
    isolated_formset.model = mocker.Mock(spec=[])
    mocker.patch.object(
        BaseTypeFormSet, "errors", new_callable=mocker.PropertyMock, return_value=[]
    )

    with pytest.raises(AttributeError, match="fund_field"):
        isolated_formset.clean()


@pytest.mark.django_db
def test_clean_does_not_tag_duplicates_when_a_form_already_has_errors(rf, main_user):
    row = {"date": "1999-9-9", "price": "5", "account": AccountFactory().pk}
    view = worth_view(rf, main_user)

    actual = bound_formset(view, [row, row, row | {"price": "x"}])

    assert not actual.is_valid()
    assert [set(form.errors) for form in actual.forms] == [set(), set(), {"price"}]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "rows",
    [
        pytest.param(["empty"], id="empty"),
        pytest.param(["filled", "deleted"], id="deleted"),
        pytest.param(["blank", "blank"], id="blank"),
    ],
)
def test_clean_skips_a_form_that_is_empty_deleted_or_blank(rf, main_user, rows):
    account = AccountFactory()
    view = worth_view(rf, main_user)

    class BlankAllowedForm(view.form_class):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["account"].required = False

    view.form_class = BlankAllowedForm
    date = unchanged_date(view)
    filled = {"date": date, "price": "5", "account": account.pk}
    posted = {
        "empty": {"date": date},
        "filled": filled,
        "deleted": filled | {"DELETE": "on"},
        "blank": {"date": date, "price": "5", "account": ""},
    }

    actual = bound_formset(view, [posted[row] for row in rows], can_delete=True)

    assert actual.is_valid()
    assert [form.errors for form in actual.forms] == [{}] * len(rows)


@pytest.mark.django_db
def test_clean_multiple_duplicates_only_tags_first_form_once(rf, main_user):
    row = {"date": "1999-9-9", "price": "5", "account": AccountFactory().pk}
    view = worth_view(rf, main_user)

    actual = bound_formset(view, [row] * 3)

    assert not actual.is_valid()
    assert [len(form.errors["account"]) for form in actual.forms] == [1, 1, 1]
