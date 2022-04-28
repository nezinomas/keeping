from django.urls import path

from . import views
from .apps import App_name

app_name = App_name

urlpatterns = [
    path(
        'counts/',
        views.Redirect.as_view(),
        name='redirect'
    ),
    path(
        'counts/none/',
        views.Empty.as_view(),
        name='empty'
    ),
    path(
        'counts/index/<slug:slug>/',
        views.Index.as_view(),
        name='index'
    ),
    path(
        'counts/list/<slug:slug>/',
        views.Lists.as_view(),
        name='list'
    ),
    path(
        'counts/history/<slug:slug>/',
        views.History.as_view(),
        name='history'
    ),
    path(
        'counts/new/<slug:slug>/',
        views.New.as_view(),
        name='new'
    ),
    path(
        'counts/update/<int:pk>/',
        views.Update.as_view(),
        name='update'
    ),
    path(
        'counts/delete/<int:pk>/',
        views.Delete.as_view(),
        name='delete'
    ),
    path(
        'counts-type/new/',
        views.TypeNew.as_view(),
        name='type_new'
    ),
    path(
        'counts-type/update/<slug:slug>/',
        views.TypeUpdate.as_view(),
        name='type_update'
    ),
    path(
        'counts-type/delete/<slug:slug>/',
        views.TypeDelete.as_view(),
        name='type_delete'
    ),
]
