from django.urls import path
from . import views

app_name = 'savings'

urlpatterns = [
    path(
        'savings/',
        views.index,
        name='savings_index'
    ),
    path(
        'savings/lists/',
        views.Lists.as_view(),
        name='savings_list'
    ),
    path(
        'savings/new/',
        views.New.as_view(),
        name='savings_new'
    ),
    path(
        'savings/update/<int:pk>/',
        views.Update.as_view(),
        name='savings_update'
    ),
    path(
        'savings/type/',
        views.TypeLists.as_view(),
        name='savings_type_list'
    ),
    path(
        'savings/type/new/',
        views.TypeNew.as_view(),
        name='savings_type_new'
    ),
    path(
        'savings/type/update/<int:pk>/',
        views.TypeUpdate.as_view(),
        name='savings_type_update'
    ),
]
