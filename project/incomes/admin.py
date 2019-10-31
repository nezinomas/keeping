from django.contrib import admin

from . import models


class IncomeAdmin(admin.ModelAdmin):
    pass


class IncomeTypeAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.IncomeType, IncomeTypeAdmin)
admin.site.register(models.Income, IncomeAdmin)
