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
        'books/new/',
        views.New.as_view(),
        name='books_new'
    ),
    path(
        'books/update/<int:pk>/',
        views.Update.as_view(),
        name='books_update'
    ),
]
