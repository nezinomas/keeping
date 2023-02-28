from django.urls import path

from . import views
from .apps import App_name

app_name = App_name


urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("info_row/", views.InfoRow.as_view(), name="info_row"),
    path("chart_readed/", views.ChartReaded.as_view(), name="chart_readed"),
    path("lists/", views.Lists.as_view(), name="list"),
    path("new/", views.New.as_view(), name="new"),
    path("update/<int:pk>/", views.Update.as_view(), name="update"),
    path("delete/<int:pk>/", views.Delete.as_view(), name="delete"),
    path("target/new/", views.TargetNew.as_view(), name="target_new"),
    path("target/update/<int:pk>/", views.TargetUpdate.as_view(), name="target_update"),
    path("search/", views.Search.as_view(), name="search"),
]
