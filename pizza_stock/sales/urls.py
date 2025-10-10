from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('', views.sales_dashboard, name='dashboard'),
    path('report/', views.sales_report, name='report'),
]