from django.urls import path

from . import views

app_name = 'books'

urlpatterns = [
    path(
        'books/',
        views.lists,
        name='books_list'
    ),
    path(
        'books/new/',
        views.new,
        name='books_new'
    ),
    path(
        'books/update/<int:pk>/',
        views.update,
        name='books_update'
    ),
]
