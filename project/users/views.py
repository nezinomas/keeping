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
        context['card_title'] = 'Log In'
        context['reset_link'] = True
        context['signup_link'] = True
        return context


    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)

        _user_settings(user)

        self.request.session['journal'] = user.journal.first()

        return HttpResponseRedirect(self.get_success_url())


class Logout(auth_views.LogoutView):
    pass


class Signup(CreateView):
    template_name = 'users/login.html'
    success_url = reverse_lazy('bookkeeping:index')
    form_class = forms.SignUpForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['submit_button_text'] = 'Sign Up'
        context['card_title'] = 'Sign Up'
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


class PasswordReset(auth_views.PasswordResetView):
    template_name = 'users/login.html'
    email_template_name = 'users/password_reset_email.html',
    subject_template_name = 'users/password_reset_subject.txt'
    success_url = reverse_lazy('users:password_reset_done')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['submit_button_text'] = 'Send password reset email'
        context['card_title'] = 'Reset your password'
        context['card_text'] = 'Enter your email address and system will send you a link to reset your pasword.'
        return context


class PasswordResetComplete(auth_views.PasswordResetCompleteView):
    template_name = 'users/password_reset_complete.html'


class PasswordResetDone(auth_views.PasswordResetDoneView):
    template_name = 'users/password_reset_done.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['card_title'] = 'Reset your password'
        context['card_text'] = 'Check your email for a link to reset your password. If it doesn\'t appear within a few minutes, check your spam folder.'
        return context


class PasswordResetConfirm(auth_views.PasswordResetConfirmView):
    template_name ='users/password_reset_confirm.html'
    success_url = reverse_lazy('users:password_reset_complete')


class PasswordChange(auth_views.PasswordChangeView):
    template_name = 'users/login.html'
    success_url = reverse_lazy('users:password_change_done')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['submit_button_text'] = 'Change password'
        context['card_title'] = 'Change password'
        return context


class PasswordChangeDone(auth_views.PasswordChangeDoneView):
    template_name = 'users/password_change_done.html'
