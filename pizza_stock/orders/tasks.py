from django.utils import timezone
from datetime import timedelta
from .models import Order
from .services import cancel_order

def auto_close_unpaid_orders():
    """
    Automatically cancel unpaid orders older than 2 hours.
    Run this every hour via cron.
    """
    cutoff_time = timezone.now() - timedelta(hours=2)
    
    old_pending_orders = Order.objects.filter(
        status='pending',
        payment_method__in=['gcash', 'paymaya'],  # Only online payment methods
        created_at__lt=cutoff_time
    )
    
    count = 0
    for order in old_pending_orders:
        try:
            cancel_order(order, reason="Auto-cancelled: Payment timeout after 2 hours")
            count += 1
        except Exception as e:
            print(f"Error cancelling order {order.order_number}: {str(e)}")
    
    print(f"Auto-cancelled {count} unpaid orders")
    return count