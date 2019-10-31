from django.contrib import admin

from . import models


class PensionAdmin(admin.ModelAdmin):
    pass


class PensionTypeAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.PensionType, PensionTypeAdmin)
admin.site.register(models.Pension, PensionAdmin)
