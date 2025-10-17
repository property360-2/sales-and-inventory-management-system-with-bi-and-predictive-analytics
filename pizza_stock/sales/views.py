from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Count
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from datetime import timedelta
from django.utils import timezone
from .models import Sale, DailySales
from .services import get_top_selling_items, get_sales_by_period, record_sale
from inventory.models import SKU, Category
from orders.models import Order, OrderItem
from orders.services import create_order, mark_order_paid
from decimal import Decimal

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
    
    # Calculate average transaction
    if sales_summary['total_orders'] and sales_summary['total_orders'] > 0:
        sales_summary['avg_transaction'] = sales_summary['total_revenue'] / sales_summary['total_orders']
    else:
        sales_summary['avg_transaction'] = 0
    
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


# ============================================
# POS / TRADITIONAL ORDERING VIEWS
# ============================================

@login_required
def pos_dashboard(request):
    """Point of Sale dashboard for creating orders"""
    branch = request.current_branch
    
    if not branch:
        messages.warning(request, 'Please select a branch.')
        return redirect('users:profile')
    
    # Get all active SKUs grouped by category
    categories = Category.objects.filter(
        is_active=True,
        skus__is_active=True
    ).prefetch_related('skus').distinct()
    
    # Get today's sales stats
    today = timezone.now().date()
    today_sales = Sale.objects.filter(
        branch=branch,
        created_at__date=today
    ).aggregate(
        total_revenue=Sum('total_amount'),
        total_orders=Count('order', distinct=True),
        total_items=Sum('quantity')
    )
    
    # Recent orders today
    recent_orders = Order.objects.filter(
        branch=branch,
        created_at__date=today
    ).order_by('-created_at')[:5]
    
    context = {
        'categories': categories,
        'today_sales': today_sales,
        'recent_orders': recent_orders,
    }
    
    return render(request, 'sales/pos_dashboard.html', context)


@login_required
@require_http_methods(["POST"])
def pos_create_order(request):
    """Create a new order from POS"""
    branch = request.current_branch
    
    if not branch:
        return JsonResponse({'success': False, 'error': 'No branch selected'}, status=400)
    
    try:
        # Get order data from request
        import json
        data = json.loads(request.body)
        
        items_data = data.get('items', [])
        customer_name = data.get('customer_name', '')
        customer_phone = data.get('customer_phone', '')
        table_number = data.get('table_number', '')
        payment_method = data.get('payment_method', 'counter')
        notes = data.get('notes', '')
        
        if not items_data:
            return JsonResponse({'success': False, 'error': 'No items in order'}, status=400)
        
        # Prepare items for order creation
        order_items = []
        for item in items_data:
            try:
                sku = SKU.objects.get(id=item['sku_id'], is_active=True)
                order_items.append({
                    'sku': sku,
                    'quantity': int(item['quantity']),
                    'notes': item.get('notes', '')
                })
            except SKU.DoesNotExist:
                return JsonResponse({
                    'success': False, 
                    'error': f'SKU {item["sku_id"]} not found'
                }, status=400)
        
        # Create the order
        with transaction.atomic():
            order = create_order(
                branch=branch,
                items_data=order_items,
                payment_method=payment_method,
                customer_info={
                    'name': customer_name,
                    'phone': customer_phone,
                    'table': table_number,
                    'notes': notes
                }
            )
            
            # If payment method is counter, mark as paid immediately
            if payment_method == 'counter':
                mark_order_paid(
                    order=order,
                    payment_method='counter',
                    reference=f'POS-{order.order_number}',
                    user=request.user
                )
        
        return JsonResponse({
            'success': True,
            'message': 'Order created successfully',
            'order_number': order.order_number,
            'order_id': order.id,
            'total_amount': float(order.total_amount),
            'receipt_url': f'/sales/pos/receipt/{order.id}/'  # FIXED URL
        })
        
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        print(f"Error creating POS order: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': 'Failed to create order'}, status=500)
@login_required
@require_http_methods(["POST"])
def pos_quick_sale(request):
    """Quick sale without creating a full order (direct inventory deduction)"""
    branch = request.current_branch
    
    if not branch:
        return JsonResponse({'success': False, 'error': 'No branch selected'}, status=400)
    
    if not request.user.is_manager():
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    try:
        import json
        data = json.loads(request.body)
        
        sku_id = data.get('sku_id')
        quantity = int(data.get('quantity', 1))
        
        if quantity <= 0:
            return JsonResponse({'success': False, 'error': 'Invalid quantity'}, status=400)
        
        sku = get_object_or_404(SKU, id=sku_id, is_active=True)
        
        # Record the sale directly
        with transaction.atomic():
            sale = record_sale(
                branch=branch,
                sku=sku,
                qty=quantity,
                price=sku.price,
                user=request.user,
                order=None  # No order for quick sales
            )
        
        return JsonResponse({
            'success': True,
            'message': f'Quick sale recorded: {quantity}x {sku.name}',
            'sale_id': sale.id,
            'total_amount': float(sale.total_amount)
        })
        
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        print(f"Error in quick sale: {e}")
        return JsonResponse({'success': False, 'error': 'Failed to record sale'}, status=500)
    
@login_required
def pos_receipt(request, order_id):
    """Display printable receipt for POS order"""
    order = get_object_or_404(Order, id=order_id)
    
    # Check access
    if not request.user.can_access_branch(order.branch):
        messages.error(request, 'Access denied.')
        return redirect('sales:pos_dashboard')
    
    return render(request, 'sales/pos_receipt.html', {'order': order})