from django.contrib import admin

from . import models


class SavingAdmin(admin.ModelAdmin):
    pass


class SavingTypeAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.SavingType, SavingTypeAdmin)
admin.site.register(models.Saving, SavingAdmin)
