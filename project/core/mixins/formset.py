from django.forms import ValidationError
from django.forms.formsets import BaseFormSet
from django.forms.models import modelformset_factory
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.translation import gettext as _

from ...core.lib import utils


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
    def _formset_initial(self):
        _list = []

        # get self.model ForeignKey field name
        foreign_key = [
            f.name for f in self.model._meta.get_fields() if (f.many_to_one)
        ]

        if not foreign_key:
            return _list

        model = self._get_type_model()
        _objects = model.objects.items()
        for _object in _objects:
            _list.append({'price': 0, foreign_key[0]: _object})

        return _list


    def _get_type_model(self):
        if not self.type_model:
            return self.model

        return self.type_model

    def _get_formset(self, post=None):
        form = self.get_form_class()
        # year = self.request.user.year
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
            initial = self._formset_initial()
            _formset = __formset(initial=initial)

            # _formset.extra += len(initial)

        return _formset

    def _get_shared_form(self, post=None):
        form = None

        if self.shared_form_class:
            form = self.shared_form_class(post)

        return form

    def post(self, request, *args, **kwargs):
        formset = self._get_formset(request.POST or None)
        shared_form = self._get_shared_form(request.POST or None)

        if formset.is_valid() and (shared_form and shared_form.is_valid()):
            data = {}
            date = shared_form.cleaned_data.get('date')

            for form in formset:
                price = form.cleaned_data.get('price')

                # if from has price and price > 0 save that form
                if float(price) > 0:
                    form.instance.date = date
                    form.save()

            context = self.get_context_data()

            data['form_is_valid'] = True
            if self.list_render_output:
                data['html_list'] = (
                    render_to_string(
                        self.get_list_template_name(), context, self.request)
                )

            if utils.is_ajax(self.request):
                return JsonResponse(data)

        return super().form_invalid(formset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['formset'] = self._get_formset(self.request.POST or None)
        context['shared_form'] = self._get_shared_form(self.request.POST or None)

        return context
