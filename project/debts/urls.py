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
        name='borrow_list'
    ),
    path(
        'borrows/return/lists/',
        views.BorrowReturnLists.as_view(),
        name='borrow_return_list'
    ),
    path(
        'lents/lists/',
        views.LentLists.as_view(),
        name='lent_list'
    ),
    path(
        'lents/return/lists/',
        views.LentReturnLists.as_view(),
        name='lent_return_list'
    ),
]
