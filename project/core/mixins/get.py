from django.core.exceptions import ObjectDoesNotExist


class GetQuerysetMixin():
    object_list = 'items'

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

    def get_object(self):
        obj = None
        pk = self.kwargs.get('pk')

        if pk:
            try:
                obj = self.model.objects.related().get(pk=pk)
            except (AttributeError, ObjectDoesNotExist):
                pass

        return obj
