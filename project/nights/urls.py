from django.urls import path

from . import views
from .apps import App_name

app_name = App_name

urlpatterns = [
    path(
        'nights/',
        views.Index.as_view(),
        name='nights_index'
    ),
    path(
        'nights/lists/',
        views.Lists.as_view(),
        name='nights_list'
    ),
    path(
        'nights/new/',
        views.New.as_view(),
        name='nights_new'
    ),
    path(
        'nights/update/<int:pk>/',
        views.Update.as_view(),
        name='nights_update'
    ),
    path(
        'nights/reload_stats/',
        views.reload_stats,
        name='reload_stats'
    ),
    path(
        'nights/history/',
        views.History.as_view(),
        name='nights_history'
    ),
]
