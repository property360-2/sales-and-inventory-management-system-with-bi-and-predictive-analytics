from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.inventory_dashboard, name="dashboard"),
    path("add/", views.add_inventory, name="add_inventory"),
    path("skus/", views.sku_list, name="sku_list"),
    path("skus/add/", views.add_sku, name="add_sku"),  # ✅ ADD THIS
    path("restock/<int:sku_id>/", views.restock_item, name="restock"),
    path("adjust/<int:sku_id>/", views.adjust_stock, name="adjust_stock"),
    path("transactions/", views.transaction_history, name="transactions"),
    path("branch-qr/<int:branch_id>/", views.branch_qr_code, name="branch_qr"),
    path("api/skus/", views.sku_list_api, name="sku_list_api"),

]
