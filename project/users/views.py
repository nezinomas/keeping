from datetime import datetime

from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.http import HttpResponseRedirect
from django.urls.base import reverse_lazy
from django.views.generic import CreateView

from ..journals.models import Journal
from . import forms


def _user_settings(user):
    save = False
    if not user.year:
        user.year = datetime.now().year
        save = True

    if not user.month:
        user.month = datetime.now().month
        save = True

    if save:
        user.save()


class Login(auth_views.LoginView):
    template_name = 'users/login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['submit_button_text'] = 'Log In'
        return context


    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)

        _user_settings(user)

        self.request.session['journal'] = user.journal.first()

        return HttpResponseRedirect(self.get_success_url())


class Signup(CreateView):
    template_name = 'users/login.html'
    success_url = reverse_lazy('bookkeeping:index')
    form_class = forms.SignUpForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['submit_button_text'] = 'Sign Up'
        return context

    def form_valid(self, form):
        valid = super().form_valid(form)

        if valid:
            user = self.object

            # First Journal user is superuser
            user.is_superuser = True

            # Create journal
            Journal.objects.create(user=user)

            # Login the user
            login(self.request, user)
            _user_settings(user)

        return valid
