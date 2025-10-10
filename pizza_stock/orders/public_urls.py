from django.urls import path
from . import views

app_name = 'orders_public'

urlpatterns = [
    # Public ordering (QR code access)
    path('<str:branch_code>/', views.public_menu, name='menu'),
    path('<str:branch_code>/cart/', views.cart_view, name='cart'),
    path('<str:branch_code>/checkout/', views.checkout_view, name='checkout'),
    
    # Cart actions
    path('api/add-to-cart/', views.add_to_cart_view, name='add_to_cart'),
    path('api/update-cart/', views.update_cart_view, name='update_cart'),
    
    # Payment
    path('payment/process/<int:payment_id>/', views.payment_process, name='payment_process'),
    path('payment/success/<int:payment_id>/', views.payment_success, name='payment_success'),
    path('payment/failed/<int:payment_id>/', views.payment_failed, name='payment_failed'),
    
    # Order tracking
    path('confirmation/<str:order_number>/', views.order_confirmation, name='order_confirmation'),
    path('status/<str:order_number>/', views.order_status, name='order_status'),
]