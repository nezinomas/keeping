from django.urls import path
from . import views

app_name = 'drinks'

urlpatterns = [
    path(
        'drinks/',
        views.lists,
        name='drinks_list'
    ),
    path(
        'drinks/new/',
        views.new,
        name='drinks_new'
    ),
    path(
        'drinks/update/<int:pk>/',
        views.update,
        name='drinks_update'
    ),
]
