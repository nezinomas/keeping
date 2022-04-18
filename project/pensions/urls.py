from django.urls import path

from . import views

app_name = 'pensions'

urlpatterns = [
    path(
        'pensions/lists/',
        views.Lists.as_view(),
        name='list'
    ),
    path(
        'pensions/new/',
        views.New.as_view(),
        name='new'
    ),
    path(
        'pensions/update/<int:pk>/',
        views.Update.as_view(),
        name='update'
    ),
    path(
        'pensions/delete/<int:pk>/',
        views.Delete.as_view(),
        name='delete'
    ),
    path(
        'pensions/type/',
        views.TypeLists.as_view(),
        name='type_list'
    ),
    path(
        'pensions/type/new/',
        views.TypeNew.as_view(),
        name='type_new'
    ),
    path(
        'pensions/type/update/<int:pk>/',
        views.TypeUpdate.as_view(),
        name='type_update'
    ),
]
