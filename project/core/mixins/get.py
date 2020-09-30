class GetQuerysetMixin():
    context_object_name = 'items'
    object_list = 'objects'

    def get_queryset(self):
        obj = self.get_object()
        if obj:
            return obj

        year = self.request.user.year

        try:
            qs = self.model.objects.year(year)
        except AttributeError:
            try:
                qs = self.model.objects.items()
            except AttributeError:
                qs = {}

        return qs

    def get_object(self):
        obj = None
        pk = self.kwargs.get('pk')
        if pk:
            obj = self.model.objects.get(pk=pk)

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        no_items = kwargs.get('no_items')
        if not no_items:
            context[self.context_object_name] = self.get_queryset()

        return context
