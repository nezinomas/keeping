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
        'counts/info_row/',
        views.InfoRow.as_view(),
        name='info_row'
    ),
    path(
        'counts/<slug:slug>/',
        views.Index.as_view(),
        name='index'
    ),
    path(
        'counts/<slug:slug>/index/',
        views.TabIndex.as_view(),
        name='tab_index'
    ),
    path(
        'counts/<slug:slug>/data/',
        views.TabData.as_view(),
        name='tab_data'
    ),
    path(
        'counts/<slug:slug>/history/',
        views.TabHistory.as_view(),
        name='tab_history'
    ),
    path(
        'counts/<slug:tab>/<slug:slug>/new/',
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
        'counts-type/update/<int:pk>/',
        views.TypeUpdate.as_view(),
        name='type_update'
    ),
    path(
        'counts-type/delete/<int:pk>/',
        views.TypeDelete.as_view(),
        name='type_delete'
    ),
]
