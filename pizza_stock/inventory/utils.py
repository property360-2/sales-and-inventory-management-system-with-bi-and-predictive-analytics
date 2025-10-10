from django.db import transaction
from django.utils import timezone
from .models import InventoryRecord, StockTransaction
import qrcode
from io import BytesIO
from django.core.files import File

@transaction.atomic
def apply_stock_transaction(branch, sku, qty, txn_type, user=None, notes=''):
    """
    Atomic stock update + create StockTransaction record.
    
    Args:
        branch: Branch instance
        sku: SKU instance
        qty: Quantity (positive for addition, negative for deduction)
        txn_type: Transaction type (restock, sale, transfer, waste, adjustment)
        user: User performing the transaction (optional)
        notes: Additional notes (optional)
    
    Returns:
        tuple: (InventoryRecord, StockTransaction)
    """
    # Get or create inventory record
    inventory, created = InventoryRecord.objects.get_or_create(
        branch=branch,
        sku=sku,
        defaults={'quantity': 0}
    )
    
    # Update quantity
    new_quantity = inventory.quantity + qty
    
    # Prevent negative stock
    if new_quantity < 0:
        raise ValueError(f"Insufficient stock. Available: {inventory.quantity}, Requested: {abs(qty)}")
    
    inventory.quantity = new_quantity
    
    # Update last restocked date for restock transactions
    if txn_type == 'restock':
        inventory.last_restocked = timezone.now()
    
    inventory.save()
    
    # Create transaction log
    transaction_log = StockTransaction.objects.create(
        branch=branch,
        sku=sku,
        quantity=qty,
        transaction_type=txn_type,
        notes=notes,
        user=user
    )
    
    return inventory, transaction_log

def generate_branch_qr(branch):
    """
    Generate QR code for branch ordering URL.
    
    Args:
        branch: Branch instance
    
    Returns:
        bool: True if successful
    """
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    # Add ordering URL
    url = f"https://pizzashop.com{branch.get_ordering_url()}"
    qr.add_data(url)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to BytesIO
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    # Save to model
    filename = f'qr_{branch.code}.png'
    branch.qr_code.save(filename, File(buffer), save=True)
    
    return True

def get_low_stock_items(branch=None):
    """
    Get all items with low stock.
    
    Args:
        branch: Branch instance (optional, if None returns for all branches)
    
    Returns:
        QuerySet: InventoryRecord queryset filtered by low stock
    """
    from django.db.models import F
    
    queryset = InventoryRecord.objects.select_related('branch', 'sku').filter(
        quantity__lt=F('safety_stock')
    )
    
    if branch:
        queryset = queryset.filter(branch=branch)
    
    return queryset.order_by('branch', 'quantity')

def transfer_stock(from_branch, to_branch, sku, qty, user):
    """
    Transfer stock between branches.
    
    Args:
        from_branch: Source Branch instance
        to_branch: Destination Branch instance
        sku: SKU instance
        qty: Quantity to transfer (positive integer)
        user: User performing the transfer
    
    Returns:
        tuple: (source_inventory, destination_inventory)
    """
    if qty <= 0:
        raise ValueError("Transfer quantity must be positive")
    
    with transaction.atomic():
        # Deduct from source
        source_inv, source_txn = apply_stock_transaction(
            branch=from_branch,
            sku=sku,
            qty=-qty,
            txn_type='transfer',
            user=user,
            notes=f'Transfer to {to_branch.name}'
        )
        
        # Add to destination
        dest_inv, dest_txn = apply_stock_transaction(
            branch=to_branch,
            sku=sku,
            qty=qty,
            txn_type='transfer',
            user=user,
            notes=f'Transfer from {from_branch.name}'
        )
        
        return source_inv, dest_inv