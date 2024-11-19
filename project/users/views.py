import contextlib
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth import views as auth_views
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls.base import reverse, reverse_lazy
from django.utils.translation import activate
from django.utils.translation import gettext as _
from django.views.generic import CreateView

from project.users import models

from ..core.mixins.views import (
    DeleteViewMixin,
    FormViewMixin,
    ListViewMixin,
    TemplateViewMixin,
    rendered_content,
)
from ..journals.forms import SettingsForm, UnnecessaryForm
from ..users.models import User
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
    template_name = "users/login.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["submit_button_text"] = _("Log in")
        context["card_title"] = _("Log in")
        context["reset_link"] = True
        context["signup_link"] = True
        context["valid_link"] = True
        return context

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)

        _user_settings(user)

        lang = user.journal.lang

        activate(lang)

        response = HttpResponseRedirect(self.get_success_url())
        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang)

        return response


class Logout(auth_views.LogoutView):
    def dispatch(self, request, *args, **kwargs):
        super().dispatch(request, *args, **kwargs)

        if request.user.is_authenticated:
            logout(request)

        return redirect(reverse("users:login"))


class Signup(CreateView):
    template_name = "users/login.html"
    success_url = reverse_lazy("bookkeeping:index")
    form_class = forms.SignUpForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["submit_button_text"] = _("Sign up")
        context["card_title"] = _("Sign up")
        context["login_link"] = True
        context["valid_link"] = True
        return context

    def form_valid(self, form):
        valid = super().form_valid(form)

        if valid:
            user = self.object
            login(self.request, user)
            _user_settings(user)

        return valid


class PasswordReset(auth_views.PasswordResetView):
    template_name = "users/login.html"
    email_template_name = ("users/password_reset_email.html",)
    subject_template_name = "users/password_reset_subject.txt"
    success_url = reverse_lazy("users:password_reset_done")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["submit_button_text"] = _("Send password reset email")
        context["card_title"] = _("Reset your password")
        context["card_text"] = _(
            "Enter your email address and system will send you a link to reset your pasword."  # noqa: E501
        )
        context["valid_link"] = True
        return context


class PasswordResetComplete(auth_views.PasswordResetCompleteView):
    template_name = "users/password_reset_complete.html"


class PasswordResetDone(auth_views.PasswordResetDoneView):
    template_name = "users/password_reset_done.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["card_title"] = _("Reset your password")
        context["card_text"] = _(
            "Check your email for a link to reset your password. If it doesn't appear within a few minutes, check your spam folder."  # noqa: E501
        )
        return context


class PasswordResetConfirm(auth_views.PasswordResetConfirmView):
    template_name = "users/password_reset_confirm.html"
    success_url = reverse_lazy("users:password_reset_complete")


class PasswordChange(auth_views.PasswordChangeView):
    template_name = "users/login.html"
    success_url = reverse_lazy("users:password_change_done")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["submit_button_text"] = _("Change password")
        context["card_title"] = _("Change password")
        context["valid_link"] = True

        return context


class PasswordChangeDone(auth_views.PasswordChangeDoneView):
    template_name = "users/password_change_done.html"


class Invite(FormViewMixin):
    template_name = "users/invite.html"
    form_class = forms.InviteForm
    success_url = reverse_lazy("users:invite_done")

    def dispatch(self, request, *args, **kwargs):
        user = request.user

        return (
            super().dispatch(request, *args, **kwargs)
            if user.is_superuser
            else redirect("bookkeeping:index")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["send"] = False
        return context

    def form_valid(self, form):
        user = self.request.user

        if form.is_valid():
            signer = TimestampSigner(salt=settings.SALT)
            secret = signer.sign_object({"jrn": user.journal.pk, "usr": user.pk})
            to_ = form.cleaned_data.get("email")
            from_ = user.email
            mail_context = {
                "username": user.username,
                "link": self.request.build_absolute_uri() + secret,
            }
            body_ = render_to_string("users/invite_email.html", mail_context)

            EmailMessage(
                subject=f"{user.username} invitation",
                body=body_,
                from_email=from_,
                to=[to_],
            ).send()

        return super().form_valid(form)


class InviteDone(TemplateViewMixin):
    template_name = "users/invite.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["send"] = True
        return context


class InviteSignup(CreateView):
    template_name = "users/login.html"
    form_class = forms.SignUpForm
    valid_link = False
    valid_days = 3

    def dispatch(self, request, *args, **kwargs):
        token = kwargs.get("token")
        signer = TimestampSigner(salt=settings.SALT)

        with contextlib.suppress(SignatureExpired, BadSignature):
            signer.unsign_object(token, max_age=timedelta(days=self.valid_days))
            self.valid_link = True

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["submit_button_text"] = _("Sign up")
        context["card_title"] = _("Sign up")
        context["login_link"] = True
        context["valid_link"] = self.valid_link
        return context

    def form_valid(self, form, **kwargs):
        user = None
        token = self.kwargs.get("token")
        signer = TimestampSigner(salt=settings.SALT)
        orig = signer.unsign_object(token, max_age=timedelta(days=self.valid_days))

        with contextlib.suppress(AttributeError, ObjectDoesNotExist):
            user = User.objects.related().get(pk=orig["usr"])

        if user:
            obj = form.save(commit=False)
            obj.journal = user.journal
            obj.save()

        return HttpResponseRedirect(reverse("users:login"))


class SettingsIndex(TemplateViewMixin):
    template_name = "users/settings_index.html"

    def dispatch(self, request, *args, **kwargs):
        user = request.user

        return (
            super().dispatch(request, *args, **kwargs)
            if user.is_superuser
            else redirect("bookkeeping:index")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "users": rendered_content(self.request, SettingsUsers, **kwargs),
                "settings_unnecessary": rendered_content(
                    self.request, SettingsUnnecessary, **kwargs
                ),
                "settings_journal": rendered_content(
                    self.request, SettingsJournal, **kwargs
                ),
            }
        )

        return context


class SettingsQueryMixin:
    def get_queryset(self):
        user = self.request.user

        return models.User.objects.related().exclude(pk=user.pk)


class SettingsUsers(SettingsQueryMixin, ListViewMixin):
    model = models.User
    template_name = "users/includes/users_lists.html"


class SettingsUsersDelete(SettingsQueryMixin, DeleteViewMixin):
    model = models.User
    template_name = "users/includes/users_delete.html"
    hx_trigger_django = "delete_user"
    success_url = reverse_lazy("users:settings_users")


class SettingsUnnecessary(FormViewMixin):
    form_class = UnnecessaryForm
    template_name = "users/includes/settings_form.html"
    url = reverse_lazy("users:settings_unnecessary")
    success_url = reverse_lazy("users:settings_unnecessary")

    def form_valid(self, form, **kwargs):
        form.save()
        return super().form_valid(form)


class SettingsJournal(FormViewMixin):
    form_class = SettingsForm
    template_name = "users/includes/settings_form.html"
    url = reverse_lazy("users:settings_journal")
    success_url = reverse_lazy("users:settings_index")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["reload_site"] = True
        return context

    def form_valid(self, form, **kwargs):
        form.save()

        response = HttpResponse(status=200, headers={"HX-Redirect": self.success_url})

        lang = form.cleaned_data.get("lang")
        activate(lang)

        response.set_cookie(
            key=settings.LANGUAGE_COOKIE_NAME,
            value=lang,
            httponly=True,
            secure=True,
            samesite="Strict",
        )

        return response
