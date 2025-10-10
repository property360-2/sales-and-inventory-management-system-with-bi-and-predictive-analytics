from django.contrib import admin
from .models import Order, OrderItem, Payment

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['unit_price']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'branch', 'customer_name', 'total_amount', 'payment_method', 'status', 'created_at']
    list_filter = ['status', 'payment_method', 'branch', 'created_at']
    search_fields = ['order_number', 'customer_name', 'customer_phone']
    readonly_fields = ['order_number', 'created_at', 'updated_at', 'paid_at', 'completed_at']
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline]

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['reference_number', 'order', 'payment_method', 'amount', 'status', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['reference_number', 'order__order_number']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'