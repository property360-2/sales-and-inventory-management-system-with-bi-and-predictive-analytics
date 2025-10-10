from django.core.mail import send_mail
from django.conf import settings
from .utils import get_low_stock_items

def send_low_stock_alerts():
    """
    Send email alerts for low stock items.
    Run this every 6 hours via cron.
    """
    low_stock_items = get_low_stock_items()
    
    if not low_stock_items.exists():
        print("No low stock items found")
        return 0
    
    # Group by branch
    branches = {}
    for item in low_stock_items:
        branch_code = item.branch.code
        if branch_code not in branches:
            branches[branch_code] = {
                'branch': item.branch,
                'items': []
            }
        branches[branch_code]['items'].append(item)
    
    # Send email per branch
    emails_sent = 0
    for branch_code, data in branches.items():
        branch = data['branch']
        items = data['items']
        
        # Build email content
        item_list = "\n".join([
            f"- {item.sku.name}: {item.quantity} units (Safety: {item.safety_stock})"
            for item in items
        ])
        
        subject = f"⚠️ Low Stock Alert - {branch.name}"
        message = f"""
Hello,

The following items are running low at {branch.name}:

{item_list}

Please restock these items as soon as possible.

Regards,
Pizza Stock Management System
        """
        
        # In production, send to branch manager's email
        # For now, just print to console
        print(f"\n{'='*50}")
        print(subject)
        print(message)
        print(f"{'='*50}\n")
        
        # Uncomment for actual email sending:
        # send_mail(
        #     subject,
        #     message,
        #     settings.DEFAULT_FROM_EMAIL,
        #     [branch.manager_email],  # Add manager_email field to Branch model
        #     fail_silently=False,
        # )
        
        emails_sent += 1
    
    print(f"Low stock alerts sent for {emails_sent} branches")
    return emails_sent