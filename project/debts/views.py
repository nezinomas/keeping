from django.urls import reverse_lazy

from ..core.mixins.views import (CreateViewMixin, DeleteViewMixin,
                                 ListViewMixin, TemplateViewMixin,
                                 UpdateViewMixin, rendered_content)
from . import forms, models


class DebtMixin():
    def get_success_url(self):
        debt_type = self.kwargs.get('debt_type')
        return reverse_lazy('debts:list', kwargs={'debt_type': debt_type})

    def get_hx_trigger(self):
        debt_type = self.kwargs.get('debt_type')
        return f'after_{debt_type}'


class DebtReturnMixin():
    def get_success_url(self):
        debt_type = self.kwargs.get('debt_type')
        return reverse_lazy('debts:return_list', kwargs={'debt_type': debt_type})

    def get_hx_trigger(self):
        debt_type = self.kwargs.get('debt_type')
        return f'after_{debt_type}_return'


class Index(TemplateViewMixin):
    template_name = 'debts/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'borrow': rendered_content(
                self.request,
                DebtLists,
                **{'debt_type': 'borrow'}),
            'borrow_return': rendered_content(
                self.request,
                DebtReturnLists,
                **{'debt_type': 'borrow'}),
            'lend': rendered_content(
                self.request,
                DebtLists,
                **{'debt_type': 'lend'}),
            'lend_return': rendered_content(
                self.request,
                DebtReturnLists,
                **{'debt_type': 'lend'}),
        })
        return context


class DebtLists(ListViewMixin):
    model = models.Debt


class DebtNew(DebtMixin, CreateViewMixin):
    model = models.Debt
    form_class = forms.DebtForm

    def url(self):
        debt_type = self.kwargs.get('debt_type')
        return reverse_lazy('debts:new', kwargs={'debt_type': debt_type})


class DebtUpdate(DebtMixin, UpdateViewMixin):
    model = models.Debt
    form_class = forms.DebtForm


class DebtDelete(DebtMixin, DeleteViewMixin):
    model = models.Debt


class DebtReturnLists(ListViewMixin):
    model = models.DebtReturn


class DebtReturnNew(DebtReturnMixin, CreateViewMixin):
    model = models.DebtReturn
    form_class = forms.DebtReturnForm

    def url(self):
        debt_type = self.kwargs.get('debt_type')
        return reverse_lazy('debts:return_new', kwargs={'debt_type': debt_type})


class DebtReturnUpdate(DebtReturnMixin, UpdateViewMixin):
    model = models.DebtReturn
    form_class = forms.DebtReturnForm


class DebtReturnDelete(DebtReturnMixin, DeleteViewMixin):
    model = models.DebtReturn
