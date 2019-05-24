from django.urls import path

from . import views

app_name = 'incomes'

urlpatterns = [
    path(
        'incomes/',
        views.lists,
        name='incomes_list'
    ),
    path(
        'incomes/new/',
        views.new,
        name='incomes_new'
    ),
    path(
        'incomes/update/<int:pk>/',
        views.update,
        name='incomes_update'
    ),
]
