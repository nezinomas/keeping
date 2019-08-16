from django.urls import path

from . import views

app_name = 'bookkeeping'

urlpatterns = [
    path('', views.Index.as_view(), name='index'),
    path('bookkeeping/saving_worth/new/', views.saving_worth_new, name='saving_worth_new')
]
