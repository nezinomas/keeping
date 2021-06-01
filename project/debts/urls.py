from django.urls import path

from . import views
from .apps import App_name

app_name = App_name


urlpatterns = [
    path(
        'debts/',
        views.Index.as_view(),
        name='debts_index'
    ),
    path(
        'borrows/lists/',
        views.BorrowLists.as_view(),
        name='borrows_list'
    ),
    path(
        'borrows/new/',
        views.BorrowNew.as_view(),
        name='borrows_new'
    ),
    path(
        'borrows/return/lists/',
        views.BorrowReturnLists.as_view(),
        name='borrows_return_list'
    ),
    path(
        'borrows/return/new/',
        views.BorrowReturnNew.as_view(),
        name='borrows_return_new'
    ),
    path(
        'lents/lists/',
        views.LentLists.as_view(),
        name='lents_list'
    ),
    path(
        'lents/new/',
        views.LentNew.as_view(),
        name='lents_new'
    ),
    path(
        'lents/return/lists/',
        views.LentReturnLists.as_view(),
        name='lents_return_list'
    ),
    path(
        'lents/return/new/',
        views.LentReturnNew.as_view(),
        name='lents_return_new'
    ),
]
