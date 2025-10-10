from django.contrib import admin
from .models import Branch, Category, SKU, InventoryRecord, StockTransaction

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'phone', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'code', 'address']
    readonly_fields = ['created_at']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']

@admin.register(SKU)
class SKUAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'is_active', 'created_at']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(InventoryRecord)
class InventoryRecordAdmin(admin.ModelAdmin):
    list_display = ['branch', 'sku', 'quantity', 'safety_stock', 'stock_status', 'updated_at']
    list_filter = ['branch']
    search_fields = ['sku__name', 'branch__name']
    readonly_fields = ['updated_at']
    
    def stock_status(self, obj):
        return obj.stock_status()
    stock_status.short_description = 'Status'

@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ['branch', 'sku', 'quantity', 'transaction_type', 'user', 'created_at']
    list_filter = ['transaction_type', 'branch', 'created_at']
    search_fields = ['sku__name', 'branch__name', 'notes']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'