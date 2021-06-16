from datetime import datetime

from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.http import HttpResponseRedirect


class CustomLogin(auth_views.LoginView):
    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)

        journal = user.journal.first()

        if not journal.year:
            journal.year = datetime.now().year
            journal.save()

        if not journal.month:
            journal.month = datetime.now().month
            journal.save()

        self.request.session['journal'] = journal

        return HttpResponseRedirect(self.get_success_url())
