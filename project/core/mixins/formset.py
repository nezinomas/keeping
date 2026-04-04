from django.core.exceptions import ImproperlyConfigured
from django.forms.models import BaseModelFormSet, modelformset_factory
from django.utils.functional import cached_property
from django.utils.translation import gettext as _

from ...bookkeeping.models import AccountWorth, PensionWorth, SavingWorth
from ...core import signals
from ...core.lib.utils import http_htmx_response

SIGNALS = {
    AccountWorth: signals.accounts_signal,
    SavingWorth: signals.savings_signal,
    PensionWorth: signals.pensions_signal,
}


class BaseTypeFormSet(BaseModelFormSet):
    def clean(self):
        # if forms have errors, don't run formset clean
        if any(self.errors):
            return

        dublicates = {}
        account_name = [
            f.name for f in self.model._meta.get_fields() if (f.many_to_one)
        ][0]

        for i, form in enumerate(self.forms):
            account = form.cleaned_data.get(account_name)
            if account in dublicates:
                msg = _("The same accounts are selected.")
                if not self.forms[dublicates[account]].errors:
                    self.forms[dublicates[account]].add_error(account_name, msg)
                self.forms[i].add_error(account_name, msg)

            dublicates[account] = i


class FormsetMixin:
    template_name = "core/generic_formset.html"
    service_class = None
    category_service_class = None

    @cached_property
    def service_instance(self):
        if self.service_class is None:
            raise ImproperlyConfigured(
                f"[{self.__class__.__module__}.{self.__class__.__name__}] is missing a data source. "
                f"Please define 'service_class'."
            )

        return self.service_class(self.request.user)

    @cached_property
    def model_class(self):
        # Dynamically grabs the model right when self.model_class is requested
        return self.service_instance.objects.model

    def formset_initial(self):
        return_list = []

        foreign_key = [
            f.name for f in self.model_class._meta.get_fields() if f.many_to_one
        ]

        if not foreign_key:
            return return_list

        items = self.category_service_class(self.request.user).items()

        return_list.extend({"price": None, foreign_key[0]: item} for item in items)
        return return_list

    def get_formset(self, post=None, **kwargs):
        initial_data = self.formset_initial()

        formset = modelformset_factory(
            model=self.model_class,
            form=self.get_formset_class(),
            formset=BaseTypeFormSet,
            extra=len(initial_data),
        )

        return (
            formset(post, **kwargs)
            if post
            else formset(
                initial=initial_data, queryset=self.model_class.objects.none(), **kwargs
            )
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

            if signal := SIGNALS.get(self.model_class):
                signal(sender=self.model_class, instance=next(iter(objects)))

        return http_htmx_response(self.get_hx_trigger_django())

    def get_context_data(self, **kwargs):
        context = {
            "formset": self.get_formset(self.request.POST or None),
            "modal_form_title": getattr(self, "modal_form_title", None),
            "modal_body_css_class": getattr(self, "modal_body_css_class", "worth-form"),
        }
        return super().get_context_data(**kwargs) | context
