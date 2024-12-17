from django.urls import path

from . import views
from .apps import App_name

app_name = App_name


urlpatterns = [
    path("year/<int:year>/", views.set_year, name="set_year"),
    path("modal/image/", views.ModalImage.as_view(), name="modal_image"),
    path(
        "set/balances/", views.RegenerateBalances.as_view(), name="regenerate_balances"
    ),
]
