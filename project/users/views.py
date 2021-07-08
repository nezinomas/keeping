from datetime import datetime, timedelta

from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.core.mail import EmailMessage
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.http import HttpResponseRedirect
from django.http.response import JsonResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls.base import reverse, reverse_lazy
from django.views.generic import CreateView

from ..config.secrets import get_secret
from ..core.mixins.ajax import AjaxCustomFormMixin
from ..core.mixins.views import IndexMixin, ListMixin
from ..users.models import User
from . import forms
from project.users import models


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
        context['valid_link'] = True
        return context


    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)

        _user_settings(user)

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
        context['login_link'] = True
        context['valid_link'] = True
        return context

    def form_valid(self, form):
        valid = super().form_valid(form)

        if valid:
            user = self.object
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
        context['valid_link'] = True
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
        context['valid_link'] = True

        return context


class PasswordChangeDone(auth_views.PasswordChangeDoneView):
    template_name = 'users/password_change_done.html'


class Invite(AjaxCustomFormMixin):
    template_name = 'users/invite.html'
    form_class = forms.InviteForm

    def dispatch(self, request, *args, **kwargs):
        user = request.user

        if not user.is_superuser:
            return redirect('bookkeeping:index')

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = self.request.user

        if form.is_valid():
            signer = TimestampSigner(salt=get_secret('SALT'))
            secret = signer.sign_object({'jrn': user.journal.pk, 'usr': user.pk })
            to_ = form.cleaned_data.get('email')
            from_ = user.email
            mail_context = {
                'username': user.username,
                'link': self.request.build_absolute_uri() + secret,
            }
            body_ = render_to_string('users/invite_email.html', mail_context)

            EmailMessage(
                subject=f'{user.username} invitation',
                body=body_,
                from_email=from_,
                to=[to_]
            ).send()

        json_data = {
            'html_form': self._render_form({'form': None}),
        }

        return JsonResponse(json_data)


class InviteSignup(CreateView):
    template_name = 'users/login.html'
    form_class = forms.SignUpForm
    valid_link = False
    valid_days = 3

    def dispatch(self, request, *args, **kwargs):
        token = kwargs.get('token')
        signer = TimestampSigner(salt=get_secret('SALT'))

        try:
            signer.unsign_object(token, max_age=timedelta(days=self.valid_days))
            self.valid_link = True
        except (SignatureExpired, BadSignature):
            pass

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['submit_button_text'] = 'Sign Up'
        context['card_title'] = 'Sign Up'
        context['login_link'] = True
        context['valid_link'] = self.valid_link
        return context

    def form_valid(self, form, **kwargs):
        token = self.kwargs.get('token')
        signer = TimestampSigner(salt=get_secret('SALT'))
        orig = signer.unsign_object(token, max_age=timedelta(days=self.valid_days))
        user = User.objects.get(pk=orig['usr'])

        obj = form.save(commit=False)
        obj.journal = user.journal
        obj.save()

        return HttpResponseRedirect(reverse('users:login'))


class SettingsIndex(IndexMixin):
    template_name = 'users/settings_index.html'

    def dispatch(self, request, *args, **kwargs):
        user = request.user

        if not user.is_superuser:
            return redirect('bookkeeping:index')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['users'] = SettingsUsers.as_view()(
            self.request, as_string=True)

        return context


class SettingsUsers(ListMixin):
    model = models.User
    template_name = 'users/includes/users_lists.html'

    def get_queryset(self):
        user = self.request.user

        return (
            models.User.objects
            .filter(journal=user.journal)
            .exclude(pk=user.pk)
        )
