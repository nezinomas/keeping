from datetime import datetime

from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.http import HttpResponseRedirect


class CustomLogin(auth_views.LoginView):
    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)

        if not user.year:
            user.year = datetime.now().year

        if not user.month:
            user.month = datetime.now().month

        user.save()

        return HttpResponseRedirect(self.get_success_url())
