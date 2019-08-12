from django.shortcuts import reverse
from django.views.generic import CreateView, ListView, UpdateView


def update_context(self, context, action):
        plural = self.model._meta.verbose_name_plural

        if action is 'update':
            context['action'] = 'update'
            context['url'] = (
                reverse(
                    f'{plural}:{plural}_update',
                    kwargs={'pk': self.object.pk}
                )
            )

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


class GetFormKwargs():
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['year'] = self.request.user.profile.year

        return kwargs


class ListMixin(GetQuerysetMixin, GetFormKwargs, ListView):
    pass


class CreateMixin(GetQuerysetMixin, GetFormKwargs, CreateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        update_context(self, context, 'create')

        return context


class UpdateMixin(GetQuerysetMixin, GetFormKwargs, UpdateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        update_context(self, context, 'update')

        return context
