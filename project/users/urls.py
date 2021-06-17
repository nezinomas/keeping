from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = 'users'


urlpatterns = [
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('login/', views.CustomLogin.as_view(), name='login'),
]
