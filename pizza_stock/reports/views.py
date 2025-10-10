from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Avg, F
from django.utils import timezone
from datetime import timedelta
from sales.models import Sale, DailySales
from orders.models import Order
from inventory.models import InventoryRecord
from inventory.utils import get_low_stock_items
from sales.services import get_top_selling_items

@login_required
def main_dashboard(request):
    """Main BI dashboard with key metrics"""
    branch = request.current_branch
    
    if not branch:
        messages.warning(request, 'Please select a branch.')
        return redirect('users:profile')
    
    # Date range
    days = int(request.GET.get('days', 7))
    start_date = timezone.now().date() - timedelta(days=days)
    
    # Sales metrics
    sales_summary = Sale.objects.filter(
        branch=branch,
        created_at__date__gte=start_date
    ).aggregate(
        total_revenue=Sum('total_amount'),
        total_transactions=Count('id'),
        total_items_sold=Sum('quantity'),
        avg_transaction=Avg('total_amount')
    )
    
    # Orders metrics
    orders_summary = Order.objects.filter(
        branch=branch,
        created_at__date__gte=start_date
    ).aggregate(
        total_orders=Count('id'),
        completed_orders=Count('id', filter=F(status='completed')),
        pending_payment=Count('id', filter=F(status='pending')),
        total_order_value=Sum('total_amount')
    )
    
    # Inventory alerts
    low_stock = get_low_stock_items(branch)
    out_of_stock = InventoryRecord.objects.filter(branch=branch, quantity=0).count()
    
    # Top selling items
    top_items = get_top_selling_items(branch=branch, days=days, limit=5)
    
    # Daily sales trend (for chart)
    daily_trends = DailySales.objects.filter(
        branch=branch,
        date__gte=start_date
    ).values('date').annotate(
        daily_total=Sum('total_amount'),
        daily_quantity=Sum('total_quantity')
    ).order_by('date')
    
    # Format for Chart.js
    chart_labels = [trend['date'].strftime('%b %d') for trend in daily_trends]
    chart_revenue = [float(trend['daily_total']) for trend in daily_trends]
    chart_quantity = [trend['daily_quantity'] for trend in daily_trends]
    
    context = {
        'sales_summary': sales_summary,
        'orders_summary': orders_summary,
        'low_stock_count': low_stock.count(),
        'low_stock_items': low_stock[:5],
        'out_of_stock_count': out_of_stock,
        'top_items': top_items,
        'days': days,
        'chart_labels': chart_labels,
        'chart_revenue': chart_revenue,
        'chart_quantity': chart_quantity,
    }
    
    return render(request, 'reports/dashboard.html', context)

@login_required
def sales_analytics(request):
    """Detailed sales analytics"""
    if not request.user.is_manager():
        messages.error(request, 'You do not have permission to view analytics.')
        return redirect('reports:dashboard')
    
    branch = request.current_branch
    
    if not branch:
        messages.warning(request, 'Please select a branch.')
        return redirect('users:profile')
    
    # Date range
    days = int(request.GET.get('days', 30))
    start_date = timezone.now().date() - timedelta(days=days)
    
    # Category performance
    from django.db.models import Sum
    from inventory.models import Category
    
    category_sales = Sale.objects.filter(
        branch=branch,
        created_at__date__gte=start_date
    ).values(
        'sku__category__name'
    ).annotate(
        total_revenue=Sum('total_amount'),
        total_quantity=Sum('quantity'),
        transaction_count=Count('id')
    ).order_by('-total_revenue')
    
    # Hourly sales pattern
    hourly_sales = Sale.objects.filter(
        branch=branch,
        created_at__date__gte=start_date
    ).extra(
        select={'hour': 'EXTRACT(hour FROM created_at)'}
    ).values('hour').annotate(
        total=Sum('total_amount'),
        count=Count('id')
    ).order_by('hour')
    
    # Payment method breakdown
    payment_breakdown = Order.objects.filter(
        branch=branch,
        created_at__date__gte=start_date,
        status__in=['paid', 'completed']
    ).values('payment_method').annotate(
        count=Count('id'),
        total=Sum('total_amount')
    )
    
    # Top customers (by phone)
    top_customers = Order.objects.filter(
        branch=branch,
        created_at__date__gte=start_date,
        customer_phone__isnull=False
    ).exclude(customer_phone='').values(
        'customer_name', 'customer_phone'
    ).annotate(
        order_count=Count('id'),
        total_spent=Sum('total_amount')
    ).order_by('-total_spent')[:10]
    
    context = {
        'category_sales': category_sales,
        'hourly_sales': list(hourly_sales),
        'payment_breakdown': payment_breakdown,
        'top_customers': top_customers,
        'days': days,
    }
    
    return render(request, 'reports/analytics.html', context)

@login_required
def inventory_report(request):
    """Inventory status report"""
    if not request.user.is_manager():
        messages.error(request, 'You do not have permission to view this report.')
        return redirect('reports:dashboard')
    
    branch = request.current_branch
    
    if not branch:
        messages.warning(request, 'Please select a branch.')
        return redirect('users:profile')
    
    # Get all inventory with stock levels
    inventory = InventoryRecord.objects.filter(
        branch=branch
    ).select_related('sku', 'sku__category').annotate(
        stock_value=F('quantity') * F('sku__price')
    ).order_by('sku__category', 'sku__name')
    
    # Calculate totals
    total_items = inventory.count()
    total_stock_value = sum(inv.stock_value for inv in inventory)
    low_stock_items = inventory.filter(quantity__lt=F('safety_stock'))
    out_of_stock_items = inventory.filter(quantity=0)
    
    context = {
        'inventory': inventory,
        'total_items': total_items,
        'total_stock_value': total_stock_value,
        'low_stock_items': low_stock_items,
        'out_of_stock_items': out_of_stock_items,
    }
    
    return render(request, 'reports/inventory.html', context)