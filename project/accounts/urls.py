from django.urls import path

from . import views
from .apps import App_name

app_name = App_name


urlpatterns = [
    path("", views.Lists.as_view(), name="list"),
    path("new/", views.New.as_view(), name="new"),
    path("update/<int:pk>/", views.Update.as_view(), name="update"),
    path("load/", views.LoadAccount.as_view(), name="load"),
]
