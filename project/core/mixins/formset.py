
from decimal import Decimal

from django.forms import ValidationError
from django.forms.formsets import BaseFormSet
from django.forms.models import modelformset_factory
from django.utils.translation import gettext as _

from ...core.mixins.views import httpHtmxResponse


class BaseTypeFormSet(BaseFormSet):
    def clean(self):
        if any(self.errors):
            return

        duplicates = False
        duplicates_list = []
        foreign_key = [
            f.name for f in self.model._meta.get_fields() if (f.many_to_one)
        ][0]

        for form in self.forms:
            if not form.cleaned_data:
                continue

            account = form.cleaned_data.get(foreign_key)
            if not account:
                continue

            if account in duplicates_list:
                duplicates = True

            if duplicates:
                raise ValidationError(_('The same accounts are selected.'))

            duplicates_list.append(account)


class FormsetMixin():
    def formset_initial(self):
        _list = []

        # get self.model ForeignKey field name
        foreign_key = [
            f.name for f in self.model._meta.get_fields() if (f.many_to_one)
        ]

        if not foreign_key:
            return _list

        model = self.get_type_model()
        _objects = model.objects.items()
        _list.extend({'price': None, foreign_key[0]: _object} for _object in _objects)

        return _list

    def get_type_model(self):
        return self.type_model or self.model

    def get_formset(self, post=None):
        form = self.get_form_class()

        __formset = (
            modelformset_factory(
                model=self.model,
                form=form,
                formset=BaseTypeFormSet,
                extra=0,
            )
        )

        return \
            __formset(post) if post else __formset(initial=self.formset_initial())

    def get_shared_form(self, post=None):
        return self.shared_form_class(post) if self.shared_form_class else None

    def post(self, request, *args, **kwargs):
        formset = self.get_formset(request.POST or None)
        shared_form = self.get_shared_form(request.POST or None)

        if formset.is_valid() and (shared_form and shared_form.is_valid()):
            date = shared_form.cleaned_data.get('date')

            for form in formset:
                price = form.cleaned_data.get('price')

                if not isinstance(price, Decimal):
                    continue

                # if from has price (price can be 0) save that form
                form.instance.date = date
                form.save()

            return httpHtmxResponse(self.get_hx_trigger_django())

        return super().form_invalid(formset)

    def get_context_data(self, **kwargs):
        context = {
            'formset': self.get_formset(self.request.POST or None),
            'shared_form': self.get_shared_form(self.request.POST or None)
        }
        return super().get_context_data(**kwargs) | context
