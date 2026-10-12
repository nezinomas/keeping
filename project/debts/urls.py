from django.urls import path, register_converter

from . import converters, views
from .apps import App_name

app_name = App_name

register_converter(converters.DebtTypeConverter, "debt_type")


urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("<debt_type:debt_type>/lists/", views.DebtLists.as_view(), name="list"),
    path("<debt_type:debt_type>/new/", views.DebtNew.as_view(), name="new"),
    path(
        "<debt_type:debt_type>/update/<int:pk>/",
        views.DebtUpdate.as_view(),
        name="update",
    ),
    path(
        "<debt_type:debt_type>/delete/<int:pk>/",
        views.DebtDelete.as_view(),
        name="delete",
    ),
    path(
        "<debt_type:debt_type>/return/lists/",
        views.DebtReturnLists.as_view(),
        name="return_list",
    ),
    path(
        "<debt_type:debt_type>/return/new/",
        views.DebtReturnNew.as_view(),
        name="return_new",
    ),
    path(
        "<debt_type:debt_type>/return/update/<int:pk>/",
        views.DebtReturnUpdate.as_view(),
        name="return_update",
    ),
    path(
        "<debt_type:debt_type>/return/delete/<int:pk>/",
        views.DebtReturnDelete.as_view(),
        name="return_delete",
    ),
]
