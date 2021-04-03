from django.urls import path

from . import views
from .apps import App_name

app_name = App_name

urlpatterns = [
    path(
        'drinks/',
        views.Index.as_view(),
        name='drinks_index'
    ),
    path(
        'drinks/lists/',
        views.Lists.as_view(),
        name='drinks_list'
    ),
    path(
        'drinks/new/',
        views.New.as_view(),
        name='drinks_new'
    ),
    path(
        'drinks/update/<int:pk>/',
        views.Update.as_view(),
        name='drinks_update'
    ),
    path(
        'drinks/delete/<int:pk>/',
        views.Delete.as_view(),
        name='drinks_delete'
    ),
    path(
        'drinks/target/lists/',
        views.TargetLists.as_view(),
        name='drinks_target_lists'
    ),
    path(
        'drinks/target/new/',
        views.TargetNew.as_view(),
        name='drinks_target_new'
    ),
    path(
        'drinks/target/update/<int:pk>/',
        views.TargetUpdate.as_view(),
        name='drinks_target_update'
    ),
    path(
        'drinks/reload_stats/',
        views.ReloadStats.as_view(),
        name='reload_stats'
    ),
    path(
        'drinks/historical_data/<int:qty>/',
        views.HistoricalData.as_view(),
        name='historical_data'
    ),
    path(
        'drinks/compare/',
        views.Compare.as_view(),
        name='compare'
    ),
    path(
        'drinks/history/',
        views.Summary.as_view(),
        name='drinks_history'
    ),
]
