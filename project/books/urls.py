from django.urls import path

from . import views
from .apps import App_name

app_name = App_name


urlpatterns = [
    path(
        'books/',
        views.Index.as_view(),
        name='index'
    ),
    path(
        'books/info_row/',
        views.InfoRow.as_view(),
        name='info_row'
    ),
    path(
        'books/chart_readed/',
        views.ChartReaded.as_view(),
        name='chart_readed'
    ),
    path(
        'books/lists/',
        views.Lists.as_view(),
        name='list'
    ),
    path(
        'books/new/',
        views.New.as_view(),
        name='new'
    ),
    path(
        'books/update/<int:pk>/',
        views.Update.as_view(),
        name='update'
    ),
    path(
        'books/delete/<int:pk>/',
        views.Delete.as_view(),
        name='delete'
    ),
    path(
        'books/target/new/',
        views.TargetNew.as_view(),
        name='target_new'
    ),
    path(
        'books/target/update/<int:pk>/',
        views.TargetUpdate.as_view(),
        name='target_update'
    ),
    path(
        'books/search/',
        views.Search.as_view(),
        name='search'
    ),
]
