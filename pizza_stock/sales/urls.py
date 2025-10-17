from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('', views.sales_dashboard, name='dashboard'),
    path('report/', views.sales_report, name='report'),
    
    # POS / Traditional Ordering
    path('pos/', views.pos_dashboard, name='pos_dashboard'),
    path('pos/create-order/', views.pos_create_order, name='pos_create_order'),
    path('pos/quick-sale/', views.pos_quick_sale, name='pos_quick_sale'),
    path('pos/receipt/<int:order_id>/', views.pos_receipt, name='pos_receipt'),  # ADD THIS
]