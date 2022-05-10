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
        views.TabData.as_view(),
        name='tab_data'
    ),
    path(
        'drinks/history/',
        views.TabHistory.as_view(),
        name='tab_history'
    ),
    path(
        'drinks/<slug:tab>/new/',
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
        'drinks/<slug:tab>/target/new/',
        views.TargetNew.as_view(),
        name='target_new'
    ),
    path(
        'drinks/target/update/<int:pk>/',
        views.TargetUpdate.as_view(),
        name='target_update'
    ),
    path(
        'drinks/compare/<int:qty>/',
        views.Compare.as_view(),
        name='compare'
    ),
    path(
        'drinks/compare/',
        views.CompareTwo.as_view(),
        name='compare_two'
    ),
    path(
        'drinks/drink_type/<str:drink_type>/',
        views.SelectDrink.as_view(),
        name='set_drink_type'
    )
]
