from django.urls import reverse_lazy

from ..accounts import views as accounts_views
from ..core.mixins.views import (CreateViewMixin, DeleteViewMixin,
                                 ListViewMixin, TemplateViewMixin,
                                 UpdateViewMixin, rendered_content)
from . import forms, models


class Index(TemplateViewMixin):
    template_name = 'transactions/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'transaction': rendered_content(self.request, Lists),
            'saving_close': rendered_content(self.request, SavingsCloseLists),
            'saving_change': rendered_content(self.request, SavingsChangeLists),
            'account': rendered_content(self.request, accounts_views.Lists),
        })
        return context


class LoadSavingType(ListViewMixin):
    template_name = 'core/dropdown.html'
    object_list = []

    def get(self, request, *args, **kwargs):
        pk = request.GET.get('from_account')

        try:
            pk = int(pk)
        except (ValueError, TypeError):
            pk = None

        if pk:
            self.object_list = \
                models.SavingType \
                .objects \
                .items() \
                .exclude(pk=pk)

        return self.render_to_response({'object_list': self.object_list})


class Lists(ListViewMixin):
    model = models.Transaction

    def get_queryset(self):
        return models.Transaction.objects.year(year=self.request.user.year)


class New(CreateViewMixin):
    model = models.Transaction
    form_class = forms.TransactionForm
    success_url = reverse_lazy('transactions:list')

    hx_trigger_django = 'afterTransaction'


class Update(UpdateViewMixin):
    model = models.Transaction
    form_class = forms.TransactionForm
    success_url = reverse_lazy('transactions:list')

    hx_trigger_django = 'afterTransaction'


class Delete(DeleteViewMixin):
    model = models.Transaction
    success_url = reverse_lazy('transactions:list')

    hx_trigger_django = 'afterTransaction'


class SavingsCloseLists(ListViewMixin):
    model = models.SavingClose

    def get_queryset(self):
        return models.SavingClose.objects.year(year=self.request.user.year)


class SavingsCloseNew(CreateViewMixin):
    model = models.SavingClose
    form_class = forms.SavingCloseForm
    success_url = reverse_lazy('transactions:savings_close_list')

    url = reverse_lazy('transactions:savings_close_new')
    hx_trigger_django = 'afterClose'


class SavingsCloseUpdate(UpdateViewMixin):
    model = models.SavingClose
    form_class = forms.SavingCloseForm
    success_url = reverse_lazy('transactions:savings_close_list')

    hx_trigger_django = 'afterClose'


class SavingsCloseDelete(DeleteViewMixin):
    model = models.SavingClose
    success_url = reverse_lazy('transactions:savings_close_list')

    hx_trigger_django = 'afterClose'


class SavingsChangeLists(ListViewMixin):
    model = models.SavingChange

    def get_queryset(self):
        return models.SavingChange.objects.year(year=self.request.user.year)


class SavingsChangeNew(CreateViewMixin):
    model = models.SavingChange
    form_class = forms.SavingChangeForm
    success_url = reverse_lazy('transactions:savings_change_list')

    url = reverse_lazy('transactions:savings_change_new')
    hx_trigger_django = 'afterChange'


class SavingsChangeUpdate(UpdateViewMixin):
    model = models.SavingChange
    form_class = forms.SavingChangeForm
    success_url = reverse_lazy('transactions:savings_change_list')

    hx_trigger_django = 'afterChange'


class SavingsChangeDelete(DeleteViewMixin):
    model = models.SavingChange
    success_url = reverse_lazy('transactions:savings_change_list')

    hx_trigger_django = 'afterChange'
