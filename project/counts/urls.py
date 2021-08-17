from django.urls import path

from . import views
from .apps import App_name

app_name = App_name

urlpatterns = [
    path(
        'counts/<slug:count_type>/',
        views.Index.as_view(),
        name='counts_index'
    ),
    path(
        'counts/lists/<slug:count_type>/',
        views.Lists.as_view(),
        name='counts_list'
    ),
    path(
        'counts/new/<slug:count_type>/',
        views.New.as_view(),
        name='counts_new'
    ),
    path(
        'counts/update/<slug:count_type>/<int:pk>/',
        views.Update.as_view(),
        name='counts_update'
    ),
    path(
        'counts/delete/<slug:count_type>/<int:pk>/',
        views.Delete.as_view(),
        name='counts_delete'
    ),
    path(
        'counts/type/new/',
        views.TypeNew.as_view(),
        name='counts_type_new'
    ),
    path(
        'counts/type/update/<int:pk>/',
        views.TypeUpdate.as_view(),
        name='counts_type_update'
    ),
    path(
        'counts/type/delete/<int:pk>/',
        views.TypeDelete.as_view(),
        name='counts_type_delete'
    ),
    path(
        'counts/reload_stats/<slug:count_type>/',
        views.ReloadStats.as_view(),
        name='reload_stats'
    ),
    path(
        'counts/history/<slug:count_type>/',
        views.History.as_view(),
        name='counts_history'
    ),
    path(
        'counts/redirect/<int:count_id>/',
        views.Redirect.as_view(),
        name='counts_redirect'
    ),
    path(
        'counts/',
        views.CountsEmpty.as_view(),
        name='counts_empty'
    ),
]
