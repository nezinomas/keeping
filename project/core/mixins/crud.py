from django.shortcuts import reverse
from django.views.generic import CreateView, ListView, UpdateView


def update_context(model, context, action):
        plural = model._meta.verbose_name_plural

        if action is 'update':
            context['action'] = 'update'
            context['url'] = reverse(f'{plural}:{plural}_update')

        if action is 'create':
            context['action'] = 'insert'
            context['url'] = reverse(f'{plural}:{plural}_new')


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


class ListMixin(GetQuerysetMixin, ListView):
    pass


class CreateMixin(GetQuerysetMixin, CreateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        update_context(self.model, context, 'create')

        return context


class UpdateMixin(GetQuerysetMixin, UpdateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        update_context(self.model, context, 'update')

        return context
