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
        'counts/<slug:slug>/index/',
        views.Index.as_view(),
        name='index'
    ),
    path(
        'counts/<slug:slug>/list/',
        views.Lists.as_view(),
        name='list'
    ),
    path(
        'counts/<slug:slug>/history/',
        views.History.as_view(),
        name='history'
    ),
    path(
        'counts/<slug:slug>/new/',
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
        'counts/type/new/',
        views.TypeNew.as_view(),
        name='type_new'
    ),
    path(
        'counts/type/<slug:slug>/update/',
        views.TypeUpdate.as_view(),
        name='type_update'
    ),
    path(
        'counts/type/<slug:slug>/delete/',
        views.TypeDelete.as_view(),
        name='type_delete'
    ),
]
