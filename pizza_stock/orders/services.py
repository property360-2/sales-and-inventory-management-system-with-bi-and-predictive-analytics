from django.db import transaction
from django.utils import timezone
from .models import Order, OrderItem, Payment
from sales.services import record_sale
import uuid

@transaction.atomic
def create_order(branch, items_data, payment_method, customer_info=None):
    """
    Create a new order with items.
    
    Args:
        branch: Branch instance
        items_data: List of dicts with 'sku', 'quantity', 'notes'
        payment_method: Payment method choice
        customer_info: Dict with customer details (optional)
    
    Returns:
        Order: Created order instance
    """
    # Create order
    order = Order.objects.create(
        branch=branch,
        payment_method=payment_method,
        customer_name=customer_info.get('name', '') if customer_info else '',
        customer_phone=customer_info.get('phone', '') if customer_info else '',
        table_number=customer_info.get('table', '') if customer_info else '',
        notes=customer_info.get('notes', '') if customer_info else '',
        total_amount=0  # Will be calculated
    )
    
    # Create order items
    for item_data in items_data:
        sku = item_data['sku']
        quantity = item_data['quantity']
        notes = item_data.get('notes', '')
        
        OrderItem.objects.create(
            order=order,
            sku=sku,
            quantity=quantity,
            unit_price=sku.price,
            notes=notes
        )
    
    # Calculate totals
    order.calculate_totals()
    
    return order

@transaction.atomic
def mark_order_paid(order, payment_method=None, reference=None, user=None):
    """
    Mark order as paid and process stock deduction.
    
    Args:
        order: Order instance
        payment_method: Payment method used (optional, uses order's if not provided)
        reference: Payment reference number (optional)
        user: User processing the payment (optional)
    
    Returns:
        Order: Updated order instance
    """
    if not order.can_mark_paid():
        raise ValueError(f"Order {order.order_number} cannot be marked as paid. Current status: {order.status}")
    
    # Update order
    order.status = 'paid'
    order.paid_at = timezone.now()
    if payment_method:
        order.payment_method = payment_method
    if reference:
        order.payment_reference = reference
    order.save()
    
    # Record sales and deduct inventory
    for item in order.items.all():
        record_sale(
            branch=order.branch,
            sku=item.sku,
            qty=item.quantity,
            price=item.unit_price,
            user=user,
            order=order
        )
    
    return order

@transaction.atomic
def cancel_order(order, reason=''):
    """
    Cancel an order.
    
    Args:
        order: Order instance
        reason: Cancellation reason
    
    Returns:
        Order: Updated order instance
    """
    if not order.can_cancel():
        raise ValueError(f"Order {order.order_number} cannot be cancelled. Current status: {order.status}")
    
    order.status = 'cancelled'
    order.notes = f"{order.notes}\n[CANCELLED] {reason}".strip()
    order.save()
    
    return order

def get_cart_from_session(session):
    """
    Get cart data from session.
    
    Args:
        session: Django session object
    
    Returns:
        dict: Cart data with items and totals
    """
    cart = session.get('cart', {})
    
    if not cart:
        return {
            'items': [],
            'subtotal': 0,
            'tax': 0,
            'total': 0,
            'count': 0
        }
    
    from inventory.models import SKU
    from decimal import Decimal
    
    items = []
    subtotal = Decimal('0')
    
    for sku_id, item_data in cart.items():
        try:
            sku = SKU.objects.get(id=sku_id, is_active=True)
            quantity = item_data['quantity']
            line_total = sku.price * quantity
            
            items.append({
                'sku': sku,
                'quantity': quantity,
                'notes': item_data.get('notes', ''),
                'line_total': line_total
            })
            
            subtotal += line_total
        except SKU.DoesNotExist:
            continue
    
    tax = subtotal * Decimal('0.12')
    total = subtotal + tax
    
    return {
        'items': items,
        'subtotal': subtotal,
        'tax': tax,
        'total': total,
        'count': sum(item['quantity'] for item in items)
    }

def add_to_cart(session, sku_id, quantity=1, notes=''):
    """Add item to session cart"""
    cart = session.get('cart', {})
    
    sku_key = str(sku_id)
    
    if sku_key in cart:
        cart[sku_key]['quantity'] += quantity
    else:
        cart[sku_key] = {
            'quantity': quantity,
            'notes': notes
        }
    
    session['cart'] = cart
    session.modified = True

def update_cart_item(session, sku_id, quantity):
    """Update cart item quantity"""
    cart = session.get('cart', {})
    sku_key = str(sku_id)
    
    if quantity <= 0:
        cart.pop(sku_key, None)
    else:
        if sku_key in cart:
            cart[sku_key]['quantity'] = quantity
    
    session['cart'] = cart
    session.modified = True

def clear_cart(session):
    """Clear the cart"""
    session['cart'] = {}
    session.modified = True