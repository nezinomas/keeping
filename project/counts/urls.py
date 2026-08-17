from django.urls import path

from . import views
from .apps import App_name

app_name = App_name

urlpatterns = [
    path("", views.Redirect.as_view(), name="redirect"),
    path("none/", views.Empty.as_view(), name="empty"),
    # counters live under c/ so a counter titled "none" or "type" cannot shadow a route
    path("c/<slug:slug>/", views.TabIndex.as_view(), name="index"),
    path("c/<slug:slug>/index/", views.TabIndex.as_view(), name="tab_index"),
    path(
        "c/<slug:slug>/periodicity/",
        views.TabPeriodicity.as_view(),
        name="tab_periodicity",
    ),
    path("c/<slug:slug>/data/", views.TabData.as_view(), name="tab_data"),
    path("c/<slug:slug>/history/", views.TabHistory.as_view(), name="tab_history"),
    path("c/<slug:tab>/<slug:slug>/new/", views.New.as_view(), name="new"),
    path("update/<int:pk>/", views.Update.as_view(), name="update"),
    path("delete/<int:pk>/", views.Delete.as_view(), name="delete"),
    path("type/new/", views.TypeNew.as_view(), name="type_new"),
    path("type/update/<int:pk>/", views.TypeUpdate.as_view(), name="type_update"),
    path("type/delete/<int:pk>/", views.TypeDelete.as_view(), name="type_delete"),
]
