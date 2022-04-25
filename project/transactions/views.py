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

    def get(self, request, *args, **kwargs):
        objects = []
        pk = request.GET.get('from_account')

        try:
            pk = int(pk)
        except (ValueError, TypeError):
            pk = None

        if pk:
            objects = (
                models.SavingType
                .objects
                .items()
                .exclude(pk=pk)
            )

        return self.render_to_response({'objects': objects})


class Lists(ListViewMixin):
    model = models.Transaction


class New(CreateViewMixin):
    model = models.Transaction
    form_class = forms.TransactionForm
    success_url = reverse_lazy('transactions:list')

    hx_trigger = 'afterTransaction'


class Update(UpdateViewMixin):
    model = models.Transaction
    form_class = forms.TransactionForm
    success_url = reverse_lazy('transactions:list')

    hx_trigger = 'afterTransaction'


class Delete(DeleteViewMixin):
    model = models.Transaction
    success_url = reverse_lazy('transactions:list')

    hx_trigger = 'afterTransaction'


class SavingsCloseLists(ListViewMixin):
    model = models.SavingClose


class SavingsCloseNew(CreateViewMixin):
    model = models.SavingClose
    form_class = forms.SavingCloseForm
    success_url = reverse_lazy('transactions:savings_close_list')

    url = reverse_lazy('transactions:savings_close_new')
    hx_trigger = 'afterClose'


class SavingsCloseUpdate(UpdateViewMixin):
    model = models.SavingClose
    form_class = forms.SavingCloseForm
    success_url = reverse_lazy('transactions:savings_close_list')

    hx_trigger = 'afterClose'


class SavingsCloseDelete(DeleteViewMixin):
    model = models.SavingClose
    success_url = reverse_lazy('transactions:savings_close_list')

    hx_trigger = 'afterClose'


class SavingsChangeLists(ListViewMixin):
    model = models.SavingChange


class SavingsChangeNew(CreateViewMixin):
    model = models.SavingChange
    form_class = forms.SavingChangeForm
    success_url = reverse_lazy('transactions:savings_change_list')

    url = reverse_lazy('transactions:savings_change_new')
    hx_trigger = 'afterChange'


class SavingsChangeUpdate(UpdateViewMixin):
    model = models.SavingChange
    form_class = forms.SavingChangeForm
    success_url = reverse_lazy('transactions:savings_change_list')

    hx_trigger = 'afterChange'


class SavingsChangeDelete(DeleteViewMixin):
    model = models.SavingChange
    success_url = reverse_lazy('transactions:savings_change_list')

    hx_trigger = 'afterChange'
