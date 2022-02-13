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
        'debts/reload/',
        views.DebtReload.as_view(),
        name='debts_reload'
    ),
    path(
        'debts/lists/',
        views.DebtLists.as_view(),
        name='debts_list'
    ),
    path(
        'debts/new/',
        views.DebtNew.as_view(),
        name='debts_new'
    ),
    path(
        'debts/update/<int:pk>/',
        views.DebtUpdate.as_view(),
        name='debts_update'
    ),
    path(
        'debts/delete/<int:pk>/',
        views.DebtDelete.as_view(),
        name='debts_delete'
    ),
    path(
        'debts/return/lists/',
        views.DebtReturnLists.as_view(),
        name='debts_return_list'
    ),
    path(
        'debts/return/new/',
        views.DebtReturnNew.as_view(),
        name='debts_return_new'
    ),
    path(
        'debts/return/update/<int:pk>/',
        views.DebtReturnUpdate.as_view(),
        name='debts_return_update'
    ),
    path(
        'debts/return/delete/<int:pk>/',
        views.DebtReturnDelete.as_view(),
        name='debts_return_delete'
    ),
]
