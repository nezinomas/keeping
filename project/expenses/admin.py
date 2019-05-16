from django.conf.locale.en import formats as en_formats
from django.contrib import admin

from . import models

en_formats.DATETIME_FORMAT = "Y-m-d H:i:s"
en_formats.DATE_FORMAT = "Y-m-d"


class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('date', 'category', 'sub_category', 'quantity', 'price', 'account')
    search_fields = ['category__title', 'sub_category__title', 'date']
    # list_per_page = 25


class ExpenseTypeAdmin(admin.ModelAdmin):
    pass


class ExpenseSubNameAdmin(admin.ModelAdmin):
    list_display = ('parent', 'title')


admin.site.register(models.Expense, ExpenseAdmin)
admin.site.register(models.ExpenseType, ExpenseTypeAdmin)
admin.site.register(models.ExpenseSubName, ExpenseSubNameAdmin)
