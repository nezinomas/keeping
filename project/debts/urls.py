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
        'debts/<str:type>/lists/',
        views.DebtLists.as_view(),
        name='debts_list'
    ),
    path(
        'debts/<str:type>/new/',
        views.DebtNew.as_view(),
        name='debts_new'
    ),
    path(
        'debts/<str:type>/update/<int:pk>/',
        views.DebtUpdate.as_view(),
        name='debts_update'
    ),
    path(
        'debts/<str:type>/delete/<int:pk>/',
        views.DebtDelete.as_view(),
        name='debts_delete'
    ),
    path(
        'debts/<str:type>/return/lists/',
        views.DebtReturnLists.as_view(),
        name='debts_return_list'
    ),
    path(
        'debts/<str:type>/return/new/',
        views.DebtReturnNew.as_view(),
        name='debts_return_new'
    ),
    path(
        'debts/<str:type>/return/update/<int:pk>/',
        views.DebtReturnUpdate.as_view(),
        name='debts_return_update'
    ),
    path(
        'debts/<str:type>/return/delete/<int:pk>/',
        views.DebtReturnDelete.as_view(),
        name='debts_return_delete'
    ),
]
