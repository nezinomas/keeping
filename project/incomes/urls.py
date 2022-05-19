from django.urls import path

from . import views

app_name = 'incomes'

urlpatterns = [
    path(
        '',
        views.Index.as_view(),
        name='index'
    ),
    path(
        'lists/',
        views.Lists.as_view(),
        name='list'
    ),
    path(
        'new/',
        views.New.as_view(),
        name='new'
    ),
    path(
        'update/<int:pk>/',
        views.Update.as_view(),
        name='update'
    ),
    path(
        'delete/<int:pk>/',
        views.Delete.as_view(),
        name='delete'
    ),
    path(
        'type/',
        views.TypeLists.as_view(),
        name='type_list'
    ),
    path(
        'type/new/',
        views.TypeNew.as_view(),
        name='type_new'
    ),
    path(
        'type/update/<int:pk>/',
        views.TypeUpdate.as_view(),
        name='type_update'
    ),
    path(
        'search/',
        views.Search.as_view(),
        name='search'
    ),
]
