class GetQuerysetMixin():
    context_object_name = 'items'
    object_list = 'objects'

    def get_queryset(self):
        year = self.request.user.year

        try:
            qs = self.model.objects.year(year)
        except AttributeError:
            try:
                qs = self.model.objects.items()
            except AttributeError:
                qs = {}

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = self.get_queryset()

        return context
