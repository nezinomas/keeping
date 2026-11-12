from django.urls import path

from . import views

app_name = "pensions"

urlpatterns = [
    path("new/", views.New.as_view(), name="new"),
    path("update/<int:pk>/", views.Update.as_view(), name="update"),
    path("delete/<int:pk>/", views.Delete.as_view(), name="delete"),
    path("type/new/", views.TypeNew.as_view(), name="type_new"),
    path("type/update/<int:pk>/", views.TypeUpdate.as_view(), name="type_update"),
]
