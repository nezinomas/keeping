from django.urls import path
from . import views

app_name = 'savings'

urlpatterns = [
    path(
        'savings/',
        views.Index.as_view(),
        name='index'
    ),
    path(
        'savings/lists/',
        views.Lists.as_view(),
        name='list'
    ),
    path(
        'savings/new/',
        views.New.as_view(),
        name='new'
    ),
    path(
        'savings/update/<int:pk>/',
        views.Update.as_view(),
        name='update'
    ),
    path(
        'savings/delete/<int:pk>/',
        views.Delete.as_view(),
        name='delete'
    ),
    path(
        'savings/type/',
        views.TypeLists.as_view(),
        name='type_list'
    ),
    path(
        'savings/type/new/',
        views.TypeNew.as_view(),
        name='type_new'
    ),
    path(
        'savings/type/update/<int:pk>/',
        views.TypeUpdate.as_view(),
        name='type_update'
    ),
]
