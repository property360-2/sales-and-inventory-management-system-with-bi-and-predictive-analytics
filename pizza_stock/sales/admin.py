from django.contrib import admin
from .models import Sale, DailySales

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['id', 'branch', 'sku', 'quantity', 'unit_price', 'total_amount', 'order', 'created_at']
    list_filter = ['created_at']
    search_fields = ['sku__name']
    readonly_fields = ['created_at', 'total_amount']
    date_hierarchy = 'created_at'

@admin.register(DailySales)
class DailySalesAdmin(admin.ModelAdmin):
    list_display = ['date', 'branch', 'sku', 'total_quantity', 'total_amount', 'transaction_count']
    list_filter = ['date']
    search_fields = ['sku__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'