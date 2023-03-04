from django.forms.formsets import BaseFormSet
from django.forms.models import modelformset_factory
from django.utils.translation import gettext as _

from ...core.mixins.views import httpHtmxResponse
from ...core import signals
from ...bookkeeping.models import AccountWorth, SavingWorth, PensionWorth

SIGNALS = {
    AccountWorth: signals.accounts_signal,
    SavingWorth: signals.savings_signal,
    PensionWorth: signals.pensions_signal,
}


class BaseTypeFormSet(BaseFormSet):
    def clean(self):
        if any(self.errors):
            # if forms have errors, don't run formset clean
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
    def formset_initial(self):
        _list = []

        # get self.model ForeignKey field name
        foreign_key = [f.name for f in self.model._meta.get_fields() if (f.many_to_one)]

        if not foreign_key:
            return _list

        model = self.get_type_model()
        _objects = model.objects.items()
        _list.extend({"price": None, foreign_key[0]: _object} for _object in _objects)

        return _list

    def get_type_model(self):
        return self.type_model or self.model

    def get_formset(self, post=None, **kwargs):
        form = self.get_form_class()
        formset = modelformset_factory(
            model=self.model,
            form=form,
            formset=BaseTypeFormSet,
            extra=0,
        )
        return formset(post) if post else formset(initial=self.formset_initial())

    def post(self, request, *args, **kwargs):
        formset = self.get_formset(request.POST or None)
        if formset.is_valid():
            objects = []
            for form in formset:
                if not form.cleaned_data.get("price"):
                    continue

                model = form.instance._meta.model  # get worth model
                form.cleaned_data["price"] *= 100  # convert price to cents
                objects.append(model(**form.cleaned_data))  # create worth object

            # if any objects, bulk_create and call signal method
            if objects:
                model.objects.bulk_create(objects)
                SIGNALS.get(model)(None, None)

            return httpHtmxResponse(self.get_hx_trigger_django())

        return super().form_invalid(formset)

    def get_context_data(self, **kwargs):
        context = {
            "formset": self.get_formset(self.request.POST or None),
        }
        return super().get_context_data(**kwargs) | context
