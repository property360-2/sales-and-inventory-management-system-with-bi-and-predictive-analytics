from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, F
from django.core.paginator import Paginator
from .models import Branch, Category, SKU, InventoryRecord, StockTransaction
from .utils import apply_stock_transaction, generate_branch_qr, get_low_stock_items

@login_required
def inventory_dashboard(request):
    """Main inventory overview"""
    branch = request.current_branch
    
    if not branch:
        messages.warning(request, 'Please select a branch.')
        return redirect('users:profile')
    
    # Get inventory for current branch
    inventory = InventoryRecord.objects.filter(
        branch=branch
    ).select_related('sku', 'sku__category').order_by('sku__category', 'sku__name')
    
    # Get low stock items
    low_stock = get_low_stock_items(branch)
    
    # Recent transactions
    recent_txns = StockTransaction.objects.filter(
        branch=branch
    ).select_related('sku', 'user')[:10]
    
    context = {
        'inventory': inventory,
        'low_stock_count': low_stock.count(),
        'low_stock_items': low_stock[:5],
        'recent_transactions': recent_txns,
        'total_items': inventory.count(),
        'out_of_stock': inventory.filter(quantity=0).count(),
    }
    
    return render(request, 'inventory/dashboard.html', context)

@login_required
def sku_list(request):
    """List all SKUs with search"""
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    
    skus = SKU.objects.select_related('category').filter(is_active=True)
    
    if query:
        skus = skus.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    
    if category_id:
        skus = skus.filter(category_id=category_id)
    
    categories = Category.objects.filter(is_active=True)
    
    paginator = Paginator(skus, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
    }
    
    return render(request, 'inventory/sku_list.html', context)

@login_required
def restock_item(request, sku_id):
    """Restock an SKU"""
    if not request.user.is_manager():
        messages.error(request, 'You do not have permission to restock items.')
        return redirect('inventory:dashboard')
    
    sku = get_object_or_404(SKU, id=sku_id)
    branch = request.current_branch
    
    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 0))
            notes = request.POST.get('notes', '')
            
            if quantity <= 0:
                messages.error(request, 'Quantity must be positive.')
            else:
                apply_stock_transaction(
                    branch=branch,
                    sku=sku,
                    qty=quantity,
                    txn_type='restock',
                    user=request.user,
                    notes=notes
                )
                messages.success(request, f'Successfully restocked {quantity} units of {sku.name}')
                return redirect('inventory:dashboard')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    context = {
        'sku': sku,
        'branch': branch,
    }
    
    return render(request, 'inventory/restock.html', context)

@login_required
def adjust_stock(request, sku_id):
    """Manual stock adjustment"""
    if not request.user.is_manager():
        messages.error(request, 'You do not have permission to adjust stock.')
        return redirect('inventory:dashboard')
    
    sku = get_object_or_404(SKU, id=sku_id)
    branch = request.current_branch
    
    try:
        inventory = InventoryRecord.objects.get(branch=branch, sku=sku)
    except InventoryRecord.DoesNotExist:
        inventory = None
    
    if request.method == 'POST':
        try:
            new_quantity = int(request.POST.get('new_quantity', 0))
            notes = request.POST.get('notes', '')
            
            if new_quantity < 0:
                messages.error(request, 'Quantity cannot be negative.')
            else:
                current_qty = inventory.quantity if inventory else 0
                adjustment = new_quantity - current_qty
                
                apply_stock_transaction(
                    branch=branch,
                    sku=sku,
                    qty=adjustment,
                    txn_type='adjustment',
                    user=request.user,
                    notes=notes
                )
                messages.success(request, f'Stock adjusted to {new_quantity} units')
                return redirect('inventory:dashboard')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    context = {
        'sku': sku,
        'branch': branch,
        'inventory': inventory,
    }
    
    return render(request, 'inventory/adjust_stock.html', context)

@login_required
def transaction_history(request):
    """View stock transaction history"""
    branch = request.current_branch
    
    txn_type = request.GET.get('type', '')
    sku_id = request.GET.get('sku', '')
    
    transactions = StockTransaction.objects.filter(
        branch=branch
    ).select_related('sku', 'user')
    
    if txn_type:
        transactions = transactions.filter(transaction_type=txn_type)
    
    if sku_id:
        transactions = transactions.filter(sku_id=sku_id)
    
    paginator = Paginator(transactions, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    skus = SKU.objects.filter(is_active=True).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'skus': skus,
        'selected_type': txn_type,
        'selected_sku': sku_id,
        'transaction_types': StockTransaction.TRANSACTION_TYPES,
    }
    
    return render(request, 'inventory/transaction_history.html', context)

@login_required
def branch_qr_code(request, branch_id):
    """Generate and view branch QR code"""
    if not request.user.is_manager():
        messages.error(request, 'You do not have permission to view QR codes.')
        return redirect('inventory:dashboard')
    
    branch = get_object_or_404(Branch, id=branch_id)
    
    if not branch.qr_code:
        try:
            generate_branch_qr(branch)
            messages.success(request, f'QR code generated for {branch.name}')
        except Exception as e:
            messages.error(request, f'Error generating QR code: {str(e)}')
    
    context = {
        'branch': branch,
    }
    
    return render(request, 'inventory/branch_qr.html', context)