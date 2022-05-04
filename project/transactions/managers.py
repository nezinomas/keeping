from django.db import models
from django.db.models import F, Sum
from django.db.models.functions import ExtractYear

from ..core.lib import utils
from ..core.mixins.queryset_sum import SumMixin


class BaseMixin(models.QuerySet):
    def related(self):
        journal = utils.get_user().journal
        return \
            self \
            .select_related('from_account', 'to_account') \
            .filter(from_account__journal=journal, to_account__journal=journal)

    def year(self, year):
        return \
            self \
            .related() \
            .filter(date__year=year)

    def items(self):
        return self.related()

    def incomes(self):
        '''
        method used only in post_save signal
        method sum prices by year
        '''
        return \
            self \
            .related() \
            .annotate(year=ExtractYear(F('date'))) \
            .values('year', 'to_account__title') \
            .annotate(incomes=Sum('price')) \
            .values('year', 'incomes', id=F('to_account__pk')) \
            .order_by('year', 'id')

    def annotate_fee(self, fee):
        if fee:
            return self.annotate(fee=F('fee'))
        return self
    annotate_fee.queryset_only = True

    def base_expenses(self, fee=False):
        '''
        method used only in post_save signal
        method sum prices by year
        '''
        values = ['year', 'expenses']

        if fee:
            values.append('fee')

        return \
            self \
            .related() \
            .annotate(year=ExtractYear(F('date'))) \
            .values('year', 'from_account__title') \
            .annotate(expenses=Sum('price')) \
            .annotate_fee(fee=fee) \
            .values(*values, id=F('from_account__pk')) \
            .order_by('year', 'id')
    base_expenses.queryset_only = True


class TransactionQuerySet(BaseMixin):
    def expenses(self):
        '''
        method used only in post_save signal
        method sum prices by year
        '''
        return self.base_expenses()


class SavingCloseQuerySet(BaseMixin, SumMixin):
    def sum_by_month(self, year, month=None):
        return \
            self \
            .related() \
            .month_sum(year=year, month=month)

    def expenses(self):
        '''
        method used only in post_save signal
        method sum prices by year
        '''
        return self.base_expenses(fee=True)


class SavingChangeQuerySet(BaseMixin):
    def expenses(self):
        '''
        method used only in post_save signal
        method sum prices by year
        '''
        return self.base_expenses(fee=True)
