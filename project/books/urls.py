from django.urls import path

from . import views

app_name = 'books'

urlpatterns = [
    path(
        'books/',
        views.Index.as_view(),
        name='books_index'
    ),
    path(
        'books/lists/',
        views.Lists.as_view(),
        name='books_list'
    ),
    path(
        'books/all/',
        views.All.as_view(),
        name='books_all'
    ),
    path(
        'books/new/',
        views.New.as_view(),
        name='books_new'
    ),
    path(
        'books/update/<int:pk>/',
        views.Update.as_view(),
        name='books_update'
    ),
    path(
        'books/delete/<int:pk>/',
        views.Delete.as_view(),
        name='books_delete'
    ),
    path(
        'books/target/lists/',
        views.TargetLists.as_view(),
        name='books_target_lists'
    ),
    path(
        'books/target/new/',
        views.TargetNew.as_view(),
        name='books_target_new'
    ),
    path(
        'books/target/update/<int:pk>/',
        views.TargetUpdate.as_view(),
        name='books_target_update'
    ),
    path(
        'books/reload_stats/',
        views.ReloadStats.as_view(),
        name='reload_stats'
    ),
    path(
        'books/search/',
        views.Search.as_view(),
        name='books_search'
    ),
]
