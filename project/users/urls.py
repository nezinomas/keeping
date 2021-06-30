from django.urls import path

from . import views

app_name = 'users'


urlpatterns = [
    path('logout/',
         views.Logout.as_view(),
         name='logout'),
    path('login/',
         views.Login.as_view(),
         name='login'),
    path('signup/',
         views.Signup.as_view(),
         name='signup'),
    path('password_reset/',
         views.PasswordReset.as_view(),
         name='password_reset'),
    path('password_reset/done/',
         views.PasswordResetDone.as_view(),
         name='password_reset_done'
    ),
    path('reset/<uidb64>/<token>/',
         views.PasswordResetConfirm.as_view(),
         name='password_reset_confirm'),
    path('reset/done/',
         views.PasswordResetComplete.as_view(),
         name='password_reset_complete'),
    path('password_change/',
         views.PasswordChange.as_view(),
         name='password_change'),
    path('password_change/done/',
         views.PasswordChangeDone.as_view(),
         name='password_change_done'),
    path('invite/',
         views.Invite.as_view(),
         name='invite'),
    path('invite/done/',
         views.InviteDone.as_view(),
         name='invite_done'),
]
