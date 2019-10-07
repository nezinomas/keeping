class GetQuerysetMixin():
    context_object_name = 'items'
    object_list = 'itms'
    month = False

    def get_queryset(self):
        year = self.request.user.profile.year
        month = self.request.user.profile.month
        try:
            if self.month:
                qs = self.model.objects.month(year, month)
            else:
                qs = self.model.objects.year(year)
        except Exception as e1:
            try:
                qs = self.model.objects.items()
            except Exception as e2:
                qs = self.model.objects.all()

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = self.get_queryset()

        return context


class GetFormKwargsMixin():
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['year'] = self.request.user.profile.year

        return kwargs
