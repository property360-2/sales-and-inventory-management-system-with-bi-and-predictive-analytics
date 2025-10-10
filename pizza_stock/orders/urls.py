from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Staff dashboard
    path('', views.orders_dashboard, name='dashboard'),
    path('<int:order_id>/', views.order_detail, name='detail'),
    path('<int:order_id>/update-status/', views.update_order_status, name='update_status'),
    path('<int:order_id>/cancel/', views.cancel_order_view, name='cancel'),
]