from django.urls import path
from . import views

app_name = 'drinks'

urlpatterns = [
    path(
        'drinks/',
        views.Lists.as_view(),
        name='drinks_list'
    ),
    path(
        'drinks/new/',
        views.New.as_view(),
        name='drinks_new'
    ),
    path(
        'drinks/update/<int:pk>/',
        views.Update.as_view(),
        name='drinks_update'
    ),
    path(
        'drinks/target/new/',
        views.TargetNew.as_view(),
        name='drinks_target_new'
    ),
    path(
        'drinks/target/update/<int:pk>/',
        views.TargetUpdate.as_view(),
        name='drinks_target_update'
    ),
]
