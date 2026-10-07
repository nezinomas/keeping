from collections.abc import Callable
from functools import partial

from django.forms.models import BaseModelFormSet, modelformset_factory
from django.utils.functional import cached_property
from django.utils.translation import gettext as _

from ...core.lib.utils import http_htmx_response
from ...core.services.signals_service import journal_user
from ...users.models import User


class BaseTypeFormSet(BaseModelFormSet):
    def clean(self):
        if any(self.errors):
            return

        relation_name = self.model.fund_field
        seen_items = {}  # Maps the account value directly to the form instance
        duplicate_msg = _("The same accounts are selected.")

        for form in self.forms:
            # Skip forms that are empty, marked for deletion, or have no dropdown value
            if not form.cleaned_data or form.cleaned_data.get("DELETE"):
                continue

            item_value = form.cleaned_data.get(relation_name)
            if not item_value:
                continue

            if item_value not in seen_items:
                seen_items[item_value] = form
                continue

            previous_form = seen_items[item_value]

            if relation_name not in previous_form.errors:
                previous_form.add_error(relation_name, duplicate_msg)

            form.add_error(relation_name, duplicate_msg)


class FormsetMixin:
    template_name = "core/generic_formset.html"
    service_class: type
    category_service_class: type
    balance_sync: Callable[[User], None]

    @cached_property
    def service_instance(self):
        return self.service_class(self.request.user)

    @cached_property
    def model_class(self):
        # Dynamically grabs the model right when self.model_class is requested
        return self.service_instance.objects.model

    def formset_initial(self):
        fund_field = self.model_class.fund_field
        items = self.category_service_class(self.request.user).items()

        return [{fund_field: item} for item in items]

    def get_formset(self, post=None, **kwargs):
        factory_blueprint = partial(
            modelformset_factory,
            model=self.model_class,
            form=self.get_formset_class(),
            formset=BaseTypeFormSet,
        )

        if post:
            formset = factory_blueprint(extra=0)
            return formset(post, **kwargs)

        # GET: Extra forms match data length, pass initial data and empty queryset
        initial_data = self.formset_initial()
        formset = factory_blueprint(extra=len(initial_data))

        return formset(
            initial=initial_data, queryset=self.model_class.objects.none(), **kwargs
        )

    def post(self, request, *args, **kwargs):
        formset = self.get_formset(request.POST or None)
        if not formset.is_valid():
            return super().form_invalid(formset)

        if objects := [
            self.model_class(**form.cleaned_data)
            for form in formset
            if form.cleaned_data.get("price") is not None
        ]:
            self.service_instance.objects.bulk_create(objects)
            self.balance_sync(journal_user(objects[0]))

        return http_htmx_response(self.get_hx_trigger_django())

    def get_context_data(self, **kwargs):
        context = {
            "formset": self.get_formset(self.request.POST or None),
            "modal_form_title": getattr(self, "modal_form_title", None),
            "modal_body_css_class": getattr(self, "modal_body_css_class", "worth-form"),
        }
        return super().get_context_data(**kwargs) | context
