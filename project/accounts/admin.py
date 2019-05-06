from django.contrib import admin

from . import models


class AccountAdmin(admin.ModelAdmin):
    pass

admin.site.register(models.Account, AccountAdmin)
