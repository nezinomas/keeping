from django.forms.models import modelformset_factory


class FormsetMixin():
    def _formset_initial(self):
        model = self._get_type_model()
        _objects = model.objects.all()
        _list = []

        # get self.model ForeignKey field name
        foreign_key = [f.name for f in self.model._meta.get_fields() if (f.many_to_one)]

        if not foreign_key:
            return _list

        for _object in _objects:
            _list.append({'price': None, foreign_key[0]: _object})

        return _list

    def _get_type_model(self):
        if not self.type_model:
            return self.model
        else:
            return self.type_model

    def _get_formset(self, post=None):
        _formset = (
            modelformset_factory(
                extra=0,
                form=self.get_form_class(),
                model=self.model,
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
            return self.form_valid(formset)
        else:
            return self.form_invalid(formset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['formset'] = self._get_formset(
            self.request.POST or None)

        return context
