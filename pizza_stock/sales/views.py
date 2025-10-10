from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Count
from datetime import timedelta
from django.utils import timezone
from .models import Sale, DailySales
from .services import get_top_selling_items, get_sales_by_period

@login_required
def sales_dashboard(request):
    """Sales overview dashboard"""
    branch = request.current_branch
    
    if not branch:
        messages.warning(request, 'Please select a branch.')
        return redirect('users:profile')
    
    # Date range
    days = int(request.GET.get('days', 7))
    start_date = timezone.now().date() - timedelta(days=days)
    
    # Sales summary
    sales_summary = Sale.objects.filter(
        branch=branch,
        created_at__date__gte=start_date
    ).aggregate(
        total_revenue=Sum('total_amount'),
        total_orders=Count('order', distinct=True),
        total_items_sold=Sum('quantity')
    )
    
    # Top selling items
    top_items = get_top_selling_items(branch=branch, days=days, limit=5)
    
    # Recent sales
    recent_sales = Sale.objects.filter(
        branch=branch
    ).select_related('sku', 'order')[:10]
    
    context = {
        'sales_summary': sales_summary,
        'top_items': top_items,
        'recent_sales': recent_sales,
        'days': days,
    }
    
    return render(request, 'sales/dashboard.html', context)

@login_required
def sales_report(request):
    """Detailed sales report"""
    branch = request.current_branch
    
    if not branch:
        messages.warning(request, 'Please select a branch.')
        return redirect('users:profile')
    
    # Date filters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    sales = get_sales_by_period(
        branch=branch,
        start_date=start_date,
        end_date=end_date
    )
    
    # Pagination
    paginator = Paginator(sales, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Summary stats
    summary = sales.aggregate(
        total_revenue=Sum('total_amount'),
        total_quantity=Sum('quantity'),
        total_transactions=Count('id')
    )
    
    context = {
        'page_obj': page_obj,
        'summary': summary,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'sales/report.html', context)