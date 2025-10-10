from django.db import transaction
from django.utils import timezone
from .models import Sale, DailySales
from inventory.utils import apply_stock_transaction

@transaction.atomic
def record_sale(branch, sku, qty, price, user=None, order=None):
    """
    Record a sale and deduct inventory.
    
    Args:
        branch: Branch instance
        sku: SKU instance
        qty: Quantity sold (positive integer)
        price: Unit price
        user: User making the sale (optional)
        order: Related Order instance (optional)
    
    Returns:
        Sale: Created sale record
    """
    # Calculate total
    total_amount = price * qty
    
    # Create sale record
    sale = Sale.objects.create(
        branch=branch,
        sku=sku,
        quantity=qty,
        unit_price=price,
        total_amount=total_amount,
        order=order,
        user=user
    )
    
    # Deduct from inventory
    apply_stock_transaction(
        branch=branch,
        sku=sku,
        qty=-qty,  # Negative for deduction
        txn_type='sale',
        user=user,
        notes=f'Sale ID: {sale.id}'
    )
    
    return sale

def aggregate_sales_daily(date=None):
    """
    Aggregate sales data for a specific date.
    Used by cron job for daily aggregation.
    
    Args:
        date: Date to aggregate (defaults to yesterday)
    
    Returns:
        int: Number of DailySales records created/updated
    """
    from django.db.models import Sum, Count, Avg
    from datetime import timedelta
    
    if date is None:
        # Default to yesterday
        date = (timezone.now() - timedelta(days=1)).date()
    
    # Get all sales for the date
    sales = Sale.objects.filter(
        created_at__date=date
    ).values('branch', 'sku').annotate(
        total_quantity=Sum('quantity'),
        total_amount=Sum('total_amount'),
        average_price=Avg('unit_price'),
        transaction_count=Count('id')
    )
    
    count = 0
    for sale_data in sales:
        DailySales.objects.update_or_create(
            branch_id=sale_data['branch'],
            sku_id=sale_data['sku'],
            date=date,
            defaults={
                'total_quantity': sale_data['total_quantity'],
                'total_amount': sale_data['total_amount'],
                'average_price': sale_data['average_price'],
                'transaction_count': sale_data['transaction_count'],
            }
        )
        count += 1
    
    return count

def get_top_selling_items(branch=None, days=7, limit=10):
    """
    Get top selling items by quantity.
    
    Args:
        branch: Branch instance (optional, None for all branches)
        days: Number of days to look back
        limit: Maximum number of items to return
    
    Returns:
        QuerySet: Top selling SKUs with sales data
    """
    from django.db.models import Sum
    from datetime import timedelta
    
    start_date = timezone.now().date() - timedelta(days=days)
    
    queryset = Sale.objects.filter(
        created_at__date__gte=start_date
    ).values(
        'sku__id', 'sku__name', 'sku__category__name'
    ).annotate(
        total_sold=Sum('quantity'),
        total_revenue=Sum('total_amount')
    ).order_by('-total_sold')
    
    if branch:
        queryset = queryset.filter(branch=branch)
    
    return queryset[:limit]

def get_sales_by_period(branch=None, start_date=None, end_date=None):
    """
    Get sales data for a specific period.
    
    Args:
        branch: Branch instance (optional)
        start_date: Start date (optional)
        end_date: End date (optional)
    
    Returns:
        QuerySet: Sales records
    """
    queryset = Sale.objects.all()
    
    if branch:
        queryset = queryset.filter(branch=branch)
    
    if start_date:
        queryset = queryset.filter(created_at__date__gte=start_date)
    
    if end_date:
        queryset = queryset.filter(created_at__date__lte=end_date)
    
    return queryset.select_related('branch', 'sku', 'sku__category')