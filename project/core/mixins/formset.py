from collections.abc import Callable

from django.forms.models import BaseModelFormSet, modelformset_factory
from django.utils.functional import cached_property

from ...core.lib.utils import http_htmx_response
from ...core.services.signals_service import journal_user
from ...users.models import User


class BaseTypeFormSet(BaseModelFormSet):
    # Only writes new rows: a posted id, any journal's or none, is never read.
    def initial_form_count(self):
        return 0

    def add_fields(self, form, index):
        super().add_fields(form, index)
        del form.fields[self.model._meta.pk.name]

    def clean(self):
        if any(self.errors):
            return

        relation_name = self.model.fund_field
        seen_items = {}
        duplicate_msg = self.form.duplicate_message

        for form in self.forms:
            if form.cleaned_data.get("DELETE"):
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
        return self.service_instance.objects.model

    @cached_property
    def funds(self):
        return list(self.category_service_class(self.request.user).items())

    def get_form_kwargs(self, **kwargs):
        return super().get_form_kwargs(**kwargs) | {"funds": self.funds}

    def formset_initial(self):
        fund_field = self.model_class.fund_field

        return [{fund_field: item} for item in self.funds]

    def formset_class(self, extra):
        return modelformset_factory(
            model=self.model_class,
            form=self.get_formset_class(),
            formset=BaseTypeFormSet,
            extra=extra,
        )

    def bound_formset(self, data):
        return self.formset_class(extra=0)(data)

    def unbound_formset(self):
        initial_data = self.formset_initial()

        return self.formset_class(extra=len(initial_data))(
            initial=initial_data, queryset=self.model_class.objects.none()
        )

    def post(self, request, *args, **kwargs):
        formset = self.bound_formset(request.POST)
        if not formset.is_valid():
            return self.render_to_response(self.get_context_data(formset=formset))

        if objects := [
            self.model_class(**form.cleaned_data)
            for form in formset
            if form.cleaned_data.get("price") is not None
        ]:
            self.service_instance.objects.bulk_create(objects)
            self.balance_sync(journal_user(objects[0]))

        return http_htmx_response(self.get_hx_trigger_django())

    def get_context_data(self, **kwargs):
        if "formset" not in kwargs:
            kwargs["formset"] = self.unbound_formset()

        return super().get_context_data(**kwargs)
