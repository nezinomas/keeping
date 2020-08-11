from django.urls import path

from . import views
from .apps import App_name

app_name = App_name

urlpatterns = [
    path(
        f'{App_name}/',
        views.Index.as_view(),
        name=f'{App_name}_index'
    ),
    path(
        f'{App_name}/lists/',
        views.Lists.as_view(),
        name=f'{App_name}_list'
    ),
    path(
        f'{App_name}/new/',
        views.New.as_view(),
        name=f'{App_name}_new'
    ),
    path(
        f'{App_name}/update/<int:pk>/',
        views.Update.as_view(),
        name=f'{App_name}_update'
    ),
    path(
        f'{App_name}/reload_stats/',
        views.reload_stats,
        name='reload_stats'
    ),
    path(
        f'{App_name}/history/',
        views.History.as_view(),
        name=f'{App_name}_history'
    ),
]
