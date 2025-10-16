from django.urls import path
from . import views

app_name = 'branches'

urlpatterns = [
    path('', views.branch_list, name='list'),
    path('create/', views.branch_create, name='create'),
    path('edit/<int:branch_id>/', views.branch_edit, name='edit'),
    path('delete/<int:branch_id>/', views.branch_delete, name='delete'),
    path('qr/<int:branch_id>/', views.branch_qr, name='qr'),
    path('stock/<int:branch_id>/', views.branch_stock_view, name='stock'),
]