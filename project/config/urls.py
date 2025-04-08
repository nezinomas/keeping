from django.urls import include, path
from django.views.defaults import page_not_found, permission_denied, server_error

from .develop_urls import urls as develop_urls

urlpatterns = [
    path("", include("project.core.urls")),
    path("", include("project.users.urls")),
    path("", include("project.bookkeeping.urls")),
    path("", include("project.transactions.urls")),
    path("accounts/", include("project.accounts.urls")),
    path("incomes/", include("project.incomes.urls")),
    path("expenses/", include("project.expenses.urls")),
    path("savings/", include("project.savings.urls")),
    path("pensions/", include("project.pensions.urls")),
    path("debts/", include("project.debts.urls")),
    path("books/", include("project.books.urls")),
    path("drinks/", include("project.drinks.urls")),
    path("counts/", include("project.counts.urls")),
    path("plans/", include("project.plans.urls")),
]


urlpatterns += [
    path(
        "403/",
        permission_denied,
        kwargs={"exception": Exception("Permission Denied")},
        name="error403",
    ),
    path(
        "404/",
        page_not_found,
        kwargs={"exception": Exception("Page not Found")},
        name="error404",
    ),
    path("500/", server_error, name="error500"),
]

urlpatterns += develop_urls
