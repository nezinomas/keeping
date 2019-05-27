from django.urls import path
from . import views

app_name = 'savings'

urlpatterns = [
    path(
        'savings/',
        views.lists,
        name='savings_list'
    ),
    path(
        'savings/new/',
        views.new,
        name='savings_new'
    ),
    path(
        'savings/update/<int:pk>/',
        views.update,
        name='savings_update'
    ),
    path(
        'savings/type/',
        views.type_lists,
        name='savings_type_list'
    ),
    path(
        'savings/type/new/',
        views.type_new,
        name='savings_type_new'
    ),
    path(
        'savings/type/update/<int:pk>/',
        views.type_update,
        name='savings_type_update'
    ),
]
