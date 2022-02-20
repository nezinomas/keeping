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
        'debts/<str:debt_type>/reload/',
        views.DebtReload.as_view(),
        name='debts_reload'
    ),
    path(
        'debts/<str:debt_type>/lists/',
        views.DebtLists.as_view(),
        name='debts_list'
    ),
    path(
        'debts/<str:debt_type>/new/',
        views.DebtNew.as_view(),
        name='debts_new'
    ),
    path(
        'debts/<str:debt_type>/update/<int:pk>/',
        views.DebtUpdate.as_view(),
        name='debts_update'
    ),
    path(
        'debts/<str:debt_type>/delete/<int:pk>/',
        views.DebtDelete.as_view(),
        name='debts_delete'
    ),
    path(
        'debts/<str:debt_type>/return/lists/',
        views.DebtReturnLists.as_view(),
        name='debts_return_list'
    ),
    path(
        'debts/<str:debt_type>/return/new/',
        views.DebtReturnNew.as_view(),
        name='debts_return_new'
    ),
    path(
        'debts/<str:debt_type>/return/update/<int:pk>/',
        views.DebtReturnUpdate.as_view(),
        name='debts_return_update'
    ),
    path(
        'debts/<str:debt_type>/return/delete/<int:pk>/',
        views.DebtReturnDelete.as_view(),
        name='debts_return_delete'
    ),
]
