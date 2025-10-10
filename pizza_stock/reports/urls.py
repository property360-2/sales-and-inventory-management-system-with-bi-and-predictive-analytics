from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('dashboard/', views.main_dashboard, name='dashboard'),
    path('analytics/', views.sales_analytics, name='analytics'),
    path('inventory/', views.inventory_report, name='inventory'),
]