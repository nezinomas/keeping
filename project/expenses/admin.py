from django.contrib import admin

from . import models


class ExpenseAdmin(admin.ModelAdmin):
    pass


class ExpenseNameAdmin(admin.ModelAdmin):
    pass


class ExpenseSubNameAdmin(admin.ModelAdmin):
    fields = ('parent', 'title')


admin.site.register(models.Expense, ExpenseAdmin)
admin.site.register(models.ExpenseName, ExpenseNameAdmin)
admin.site.register(models.ExpenseSubName, ExpenseSubNameAdmin)
