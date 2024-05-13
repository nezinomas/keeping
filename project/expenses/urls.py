from django.urls import path

from .apps import App_name
from .views import expenses, expenses_name, expenses_type

app_name = App_name


urlpatterns = [
    path("", expenses.Index.as_view(), name="index"),
    path("<int:month>/", expenses.Index.as_view(), name="index"),
    path("list/", expenses.Lists.as_view(), name="list"),
    path("list/<int:month>/", expenses.Lists.as_view(), name="list"),
    path("new/", expenses.New.as_view(), name="new"),
    path("update/<int:pk>/", expenses.Update.as_view(), name="update"),
    path("delete/<int:pk>/", expenses.Delete.as_view(), name="delete"),
    path(
        "load_expense_name/",
        expenses.LoadExpenseName.as_view(),
        name="load_expense_name",
    ),
    path("search/", expenses.Search.as_view(), name="search"),
    path("type/new/", expenses_type.New.as_view(), name="type_new"),
    path("type/", expenses_type.Lists.as_view(), name="type_list"),
    path("type/update/<int:pk>/", expenses_type.Update.as_view(), name="type_update"),
    path("name/new/", expenses_name.New.as_view(), name="name_new"),
    path("name/update/<int:pk>/", expenses_name.Update.as_view(), name="name_update"),
]
