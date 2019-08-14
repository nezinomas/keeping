from django.urls import path

from . import views

app_name = 'incomes'

urlpatterns = [
    path(
        'incomes/',
        views.index,
        name='incomes_index'
    ),
    path(
        'incomes/lists/',
        views.Lists.as_view(),
        name='incomes_list'
    ),
    path(
        'incomes/new/',
        views.New.as_view(),
        name='incomes_new'
    ),
    path(
        'incomes/update/<int:pk>/',
        views.Update.as_view(),
        name='incomes_update'
    ),
    path(
        'incomes/type/',
        views.TypeLists.as_view(),
        name='incomes_type_list'
    ),
    path(
        'incomes/type/new/',
        views.TypeNew.as_view(),
        name='incomes_type_new'
    ),
    path(
        'incomes/type/update/<int:pk>/',
        views.TypeUpdate.as_view(),
        name='incomes_type_update'
    ),
]
