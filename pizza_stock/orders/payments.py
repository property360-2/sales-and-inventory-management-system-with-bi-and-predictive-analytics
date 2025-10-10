"""
Demo payment gateway simulation for GCash and PayMaya.
This is NOT a real payment integration - for demo purposes only.
"""

import uuid
from django.utils import timezone
from .models import Payment

def initiate_payment(order, payment_method):
    """
    Simulate payment initiation.
    
    Args:
        order: Order instance
        payment_method: 'gcash' or 'paymaya'
    
    Returns:
        dict: Payment details with reference and redirect URL
    """
    # Generate fake reference number
    reference = f"{payment_method.upper()}-{uuid.uuid4().hex[:12].upper()}"
    
    # Create payment record
    payment = Payment.objects.create(
        order=order,
        payment_method=payment_method,
        amount=order.total_amount,
        reference_number=reference,
        status='processing'
    )
    
    # In real implementation, this would call actual payment API
    # and get a redirect URL from the payment gateway
    
    return {
        'reference': reference,
        'payment_id': payment.id,
        'redirect_url': f'/order/payment/process/{payment.id}/',
        'amount': order.total_amount,
        'order_number': order.order_number
    }

def process_payment_callback(payment_id, status='success', gateway_response=None):
    """
    Process payment callback/webhook.
    In real implementation, this would verify the webhook signature.
    
    Args:
        payment_id: Payment instance ID
        status: 'success' or 'failed'
        gateway_response: Dict with gateway response data
    
    Returns:
        Payment: Updated payment instance
    """
    try:
        payment = Payment.objects.get(id=payment_id)
        
        if status == 'success':
            payment.status = 'success'
            payment.gateway_response = gateway_response or {
                'simulated': True,
                'timestamp': timezone.now().isoformat()
            }
            payment.save()
            
            # Mark order as paid
            from .services import mark_order_paid
            mark_order_paid(
                order=payment.order,
                payment_method=payment.payment_method,
                reference=payment.reference_number
            )
        else:
            payment.status = 'failed'
            payment.gateway_response = gateway_response or {
                'simulated': True,
                'error': 'Payment declined',
                'timestamp': timezone.now().isoformat()
            }
            payment.save()
        
        return payment
    except Payment.DoesNotExist:
        raise ValueError(f"Payment {payment_id} not found")

def simulate_payment_success(payment_id):
    """Simulate successful payment (for demo)"""
    return process_payment_callback(payment_id, status='success')

def simulate_payment_failure(payment_id):
    """Simulate failed payment (for demo)"""
    return process_payment_callback(payment_id, status='failed')

def get_payment_status(reference_number):
    """
    Check payment status by reference number.
    
    Args:
        reference_number: Payment reference
    
    Returns:
        dict: Payment status info
    """
    try:
        payment = Payment.objects.get(reference_number=reference_number)
        return {
            'status': payment.status,
            'order_number': payment.order.order_number,
            'amount': payment.amount,
            'created_at': payment.created_at,
        }
    except Payment.DoesNotExist:
        return None