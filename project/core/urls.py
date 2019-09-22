from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('set/year/<int:year>/<str:view_name>/', views.set_year, name='set_year'),
    path('set/month/<int:month>/', views.set_month, name='set_month'),
]
