from django.forms.models import modelformset_factory
from django.http import JsonResponse
from django.template.loader import render_to_string


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
        _formset = (
            modelformset_factory(
                extra=0,
                form=form,
                model=self.model
            )
        )

        if post:
            _formset = _formset(post)
        else:
            initial = self._formset_initial()
            _formset = _formset(
                queryset=self.model.objects.none(),
                initial=initial)

            _formset.extra += len(initial)

        return _formset

    def post(self, request, *args, **kwargs):
        formset = self._get_formset(request.POST or None)
        if formset.is_valid():
            data = dict()

            # if from has price and price > 0 save that form
            for form in formset:
                price = form.cleaned_data.get('price')

                if float(price) > 0:
                    form.save()

            context = self.get_context_data()

            data['form_is_valid'] = True
            if self.list_render_output:
                data['html_list'] = (
                    render_to_string(
                        self.get_list_template_name(), context, self.request)
                )

            if self.request.is_ajax():
                return JsonResponse(data)

        return super().form_invalid(formset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['formset'] = self._get_formset(
            self.request.POST or None)

        return context
