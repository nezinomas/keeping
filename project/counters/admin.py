from django.contrib import admin

from . import models


class CounterTypeAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.CounterType, CounterTypeAdmin)
