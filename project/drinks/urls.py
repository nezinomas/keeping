from django.urls import path

from . import views
from .apps import App_name

app_name = App_name

urlpatterns = [
    path(
        'drinks/',
        views.Index.as_view(),
        name='index'
    ),
    path(
        'drinks/index/',
        views.TabIndex.as_view(),
        name='tab_index'
    ),
    path(
        'drinks/data/',
        views.Lists.as_view(),
        name='tab_data'
    ),
    path(
        'drinks/history/',
        views.Summary.as_view(),
        name='tab_history'
    ),
    path(
        'drinks/new/',
        views.New.as_view(),
        name='new'
    ),
    path(
        'drinks/update/<int:pk>/',
        views.Update.as_view(),
        name='update'
    ),
    path(
        'drinks/delete/<int:pk>/',
        views.Delete.as_view(),
        name='delete'
    ),
    path(
        'drinks/target/lists/',
        views.TargetLists.as_view(),
        name='target_list'
    ),
    path(
        'drinks/target/new/',
        views.TargetNew.as_view(),
        name='target_new'
    ),
    path(
        'drinks/target/update/<int:pk>/',
        views.TargetUpdate.as_view(),
        name='target_update'
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
        'drinks/drink_type/<str:drink_type>/',
        views.SelectDrink.as_view(),
        name='set_drink_type'
    )
]
