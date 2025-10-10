from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from inventory.models import Branch, SKU, Category
from .models import Order, Payment
from .services import (
    create_order, mark_order_paid, cancel_order,
    get_cart_from_session, add_to_cart, update_cart_item, clear_cart
)
from .payments import initiate_payment, simulate_payment_success, simulate_payment_failure

# ============================================
# PUBLIC ORDERING VIEWS (Customer-facing)
# ============================================

def public_menu(request, branch_code):
    """Public menu for QR code ordering"""
    branch = get_object_or_404(Branch, code=branch_code, is_active=True)
    
    # Get active categories and SKUs
    categories = Category.objects.filter(is_active=True).prefetch_related('skus')
    
    # Get cart info
    cart = get_cart_from_session(request.session)
    
    context = {
        'branch': branch,
        'categories': categories,
        'cart': cart,
    }
    
    return render(request, 'orders/public/menu.html', context)

@require_http_methods(["POST"])
def add_to_cart_view(request):
    """Add item to cart via AJAX"""
    sku_id = request.POST.get('sku_id')
    quantity = int(request.POST.get('quantity', 1))
    notes = request.POST.get('notes', '')
    
    try:
        sku = SKU.objects.get(id=sku_id, is_active=True)
        add_to_cart(request.session, sku_id, quantity, notes)
        
        cart = get_cart_from_session(request.session)
        
        return JsonResponse({
            'success': True,
            'message': f'{sku.name} added to cart',
            'cart_count': cart['count'],
            'cart_total': float(cart['total'])
        })
    except SKU.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Item not found'
        }, status=404)

def cart_view(request, branch_code):
    """View cart"""
    branch = get_object_or_404(Branch, code=branch_code, is_active=True)
    cart = get_cart_from_session(request.session)
    
    context = {
        'branch': branch,
        'cart': cart,
    }
    
    return render(request, 'orders/public/cart.html', context)

@require_http_methods(["POST"])
def update_cart_view(request):
    """Update cart item quantity"""
    sku_id = request.POST.get('sku_id')
    quantity = int(request.POST.get('quantity', 0))
    
    update_cart_item(request.session, sku_id, quantity)
    cart = get_cart_from_session(request.session)
    
    return JsonResponse({
        'success': True,
        'cart_count': cart['count'],
        'cart_total': float(cart['total'])
    })

def checkout_view(request, branch_code):
    """Checkout page"""
    branch = get_object_or_404(Branch, code=branch_code, is_active=True)
    cart = get_cart_from_session(request.session)
    
    if not cart['items']:
        messages.warning(request, 'Your cart is empty.')
        return redirect('orders_public:menu', branch_code=branch_code)
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        customer_name = request.POST.get('customer_name', '')
        customer_phone = request.POST.get('customer_phone', '')
        table_number = request.POST.get('table_number', '')
        notes = request.POST.get('notes', '')
        
        try:
            # Prepare items data
            items_data = [
                {
                    'sku': item['sku'],
                    'quantity': item['quantity'],
                    'notes': item['notes']
                }
                for item in cart['items']
            ]
            
            # Create order
            order = create_order(
                branch=branch,
                items_data=items_data,
                payment_method=payment_method,
                customer_info={
                    'name': customer_name,
                    'phone': customer_phone,
                    'table': table_number,
                    'notes': notes
                }
            )
            
            # Clear cart
            clear_cart(request.session)
            
            # Handle payment method
            if payment_method == 'counter':
                # Pay at counter - order stays pending
                messages.success(request, f'Order #{order.order_number} created! Please pay at the counter.')
                return redirect('orders_public:order_confirmation', order_number=order.order_number)
            else:
                # Online payment (GCash/PayMaya)
                payment_data = initiate_payment(order, payment_method)
                return redirect('orders_public:payment_process', payment_id=payment_data['payment_id'])
                
        except Exception as e:
            messages.error(request, f'Error creating order: {str(e)}')
    
    context = {
        'branch': branch,
        'cart': cart,
    }
    
    return render(request, 'orders/public/checkout.html', context)

def payment_process(request, payment_id):
    """Simulate payment processing page"""
    payment = get_object_or_404(Payment, id=payment_id)
    
    context = {
        'payment': payment,
        'order': payment.order,
        'branch': payment.order.branch,
    }
    
    return render(request, 'orders/public/payment_process.html', context)

def payment_success(request, payment_id):
    """Handle successful payment (demo)"""
    payment = get_object_or_404(Payment, id=payment_id)
    
    # Simulate payment success
    simulate_payment_success(payment_id)
    
    messages.success(request, f'Payment successful! Order #{payment.order.order_number} confirmed.')
    return redirect('orders_public:order_confirmation', order_number=payment.order.order_number)

def payment_failed(request, payment_id):
    """Handle failed payment (demo)"""
    payment = get_object_or_404(Payment, id=payment_id)
    
    # Simulate payment failure
    simulate_payment_failure(payment_id)
    
    messages.error(request, 'Payment failed. Please try again.')
    return redirect('orders_public:checkout', branch_code=payment.order.branch.code)

def order_confirmation(request, order_number):
    """Order confirmation page"""
    order = get_object_or_404(Order, order_number=order_number)
    
    context = {
        'order': order,
        'branch': order.branch,
    }
    
    return render(request, 'orders/public/confirmation.html', context)

def order_status(request, order_number):
    """Check order status"""
    order = get_object_or_404(Order, order_number=order_number)
    
    context = {
        'order': order,
        'branch': order.branch,
    }
    
    return render(request, 'orders/public/status.html', context)

# ============================================
# STAFF VIEWS (Login required)
# ============================================

@login_required
def orders_dashboard(request):
    """Staff orders dashboard"""
    branch = request.current_branch
    
    if not branch:
        messages.warning(request, 'Please select a branch.')
        return redirect('users:profile')
    
    # Filter by status
    status = request.GET.get('status', '')
    
    orders = Order.objects.filter(branch=branch).select_related('branch').prefetch_related('items')
    
    if status:
        orders = orders.filter(status=status)
    else:
        # Default: show active orders (not completed/cancelled)
        orders = orders.exclude(status__in=['completed', 'cancelled'])
    
    # Order by creation (newest first)
    orders = orders.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Summary stats
    summary = {
        'pending': Order.objects.filter(branch=branch, status='pending').count(),
        'paid': Order.objects.filter(branch=branch, status='paid').count(),
        'preparing': Order.objects.filter(branch=branch, status='preparing').count(),
        'ready': Order.objects.filter(branch=branch, status='ready').count(),
    }
    
    context = {
        'page_obj': page_obj,
        'summary': summary,
        'selected_status': status,
        'status_choices': Order.STATUS_CHOICES,
    }
    
    return render(request, 'orders/staff/dashboard.html', context)

@login_required
def order_detail(request, order_id):
    """View order details"""
    order = get_object_or_404(Order, id=order_id)
    
    # Check access
    if not request.user.can_access_branch(order.branch):
        messages.error(request, 'You do not have access to this order.')
        return redirect('orders:dashboard')
    
    context = {
        'order': order,
    }
    
    return render(request, 'orders/staff/detail.html', context)

@login_required
@require_http_methods(["POST"])
def update_order_status(request, order_id):
    """Update order status"""
    if not request.user.is_manager():
        return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
    
    order = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get('status')
    
    if new_status not in dict(Order.STATUS_CHOICES):
        return JsonResponse({'success': False, 'message': 'Invalid status'}, status=400)
    
    try:
        # Special handling for marking as paid
        if new_status == 'paid' and order.status == 'pending':
            mark_order_paid(order, user=request.user)
            message = f'Order #{order.order_number} marked as paid'
        else:
            order.status = new_status
            order.save()
            message = f'Order status updated to {order.get_status_display()}'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'new_status': order.status,
            'new_status_display': order.get_status_display()
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

@login_required
def cancel_order_view(request, order_id):
    """Cancel an order"""
    if not request.user.is_manager():
        messages.error(request, 'You do not have permission to cancel orders.')
        return redirect('orders:dashboard')
    
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        try:
            cancel_order(order, reason)
            messages.success(request, f'Order #{order.order_number} cancelled.')
        except ValueError as e:
            messages.error(request, str(e))
        
        return redirect('orders:dashboard')
    
    context = {
        'order': order,
    }
    
    return render(request, 'orders/staff/cancel.html', context)