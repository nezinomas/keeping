class GetQuerysetMixin():
    context_object_name = 'items'

    def get_queryset(self):
        try:
            qs = self.model.objects.year(self.request.user.profile.year)
        except Exception as e1:
            try:
                qs = self.model.objects.items()
            except Exception as e2:
                qs = self.model.objects.all()

        return qs


class GetFormKwargsMixin():
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['year'] = self.request.user.profile.year

        return kwargs
