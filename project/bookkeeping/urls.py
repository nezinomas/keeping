from django.urls import path

from . import views

app_name = 'bookkeeping'

urlpatterns = [
    path('', views.index, name='index'),
    path('bookkeeping/saving_worth/new/', views.saving_worth_new, name='saving_worth_new')
]
