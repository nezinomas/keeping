from django.urls import path

from . import views
from .apps import App_name

app_name = App_name

urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("index/", views.TabIndex.as_view(), name="tab_index"),
    path("data/", views.TabData.as_view(), name="tab_data"),
    path("history/", views.TabHistory.as_view(), name="tab_history"),
    path("<slug:tab>/new/", views.New.as_view(), name="new"),
    path("update/<int:pk>/", views.Update.as_view(), name="update"),
    path("delete/<int:pk>/", views.Delete.as_view(), name="delete"),
    path("target/lists/", views.TargetLists.as_view(), name="target_list"),
    path("<slug:tab>/target/new/", views.TargetNew.as_view(), name="target_new"),
    path("target/update/<int:pk>/", views.TargetUpdate.as_view(), name="target_update"),
    path("compare/<int:qty>/", views.Compare.as_view(), name="compare"),
    path("compare/", views.CompareTwo.as_view(), name="compare_two"),
    path(
        "drink_type/<str:drink_type>/",
        views.SelectDrink.as_view(),
        name="set_drink_type",
    ),
]
