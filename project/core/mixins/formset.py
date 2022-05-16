import json

from django.forms import ValidationError
from django.forms.formsets import BaseFormSet
from django.forms.models import modelformset_factory
from django.http import HttpResponse
from django.utils.translation import gettext as _


class BaseTypeFormSet(BaseFormSet):
    def clean(self):
        if any(self.errors):
            return

        arr = []
        duplicates = False

        for form in self.forms:
            if form.cleaned_data:
                _types = ['account', 'saving_type', 'pension_type']
                for _type in _types:
                    _account = form.cleaned_data.get(_type)
                    if not _account:
                        continue

                    if _account in arr:
                        duplicates = True
                    arr.append(_account)

                    if duplicates:
                        raise ValidationError(_('The same accounts are selected.'))


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
        for _object in _objects:
            _list.append({'price': 0, foreign_key[0]: _object})

        return _list

    def get_type_model(self):
        if not self.type_model:
            return self.model

        return self.type_model

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

        if post:
            _formset = __formset(post)
        else:
            initial = self.formset_initial()
            _formset = __formset(initial=initial)

        return _formset

    def get_shared_form(self, post=None):
        form = None

        if self.shared_form_class:
            form = self.shared_form_class(post)

        return form

    def post(self, request, *args, **kwargs):
        formset = self.get_formset(request.POST or None)
        shared_form = self.get_shared_form(request.POST or None)

        if formset.is_valid() and (shared_form and shared_form.is_valid()):
            date = shared_form.cleaned_data.get('date')

            for form in formset:
                price = form.cleaned_data.get('price')

                # if from has price and price > 0 save that form
                if float(price) > 0:
                    form.instance.date = date
                    form.save()

            return HttpResponse(
                status=204,
                headers={
                    'HX-Trigger': json.dumps({self.get_hx_trigger_django(): None}),
                },
            )

        return super().form_invalid(formset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['formset'] = self.get_formset(self.request.POST or None)
        context['shared_form'] = self.get_shared_form(self.request.POST or None)

        return context


