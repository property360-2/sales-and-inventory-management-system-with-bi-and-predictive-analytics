from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, F
from django.core.paginator import Paginator
from inventory.models import Branch, Category, InventoryRecord, StockTransaction
from inventory.utils import generate_branch_qr

@login_required
def branch_list(request):
    """List all branches (admin only)"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to manage branches.')
        return redirect('reports:dashboard')
    
    branches = Branch.objects.all().order_by('name')
    
    context = {
        'branches': branches,
        'total_branches': branches.count(),
        'active_branches': branches.filter(is_active=True).count(),
        'inactive_branches': branches.filter(is_active=False).count(),
    }
    
    return render(request, 'branches/branch_list.html', context)

@login_required
def branch_create(request):
    """Create new branch (admin only)"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to create branches.')
        return redirect('reports:dashboard')
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            code = request.POST.get('code').upper()
            address = request.POST.get('address')
            phone = request.POST.get('phone')
            is_active = request.POST.get('is_active') == 'on'
            
            # Validation
            if Branch.objects.filter(code=code).exists():
                messages.error(request, f'Branch code "{code}" already exists.')
                return redirect('branches:create')
            
            # Create branch
            with transaction.atomic():
                branch = Branch.objects.create(
                    name=name,
                    code=code,
                    address=address,
                    phone=phone,
                    is_active=is_active
                )
                
                # Generate QR code
                try:
                    generate_branch_qr(branch)
                except Exception as e:
                    print(f"QR generation error: {e}")
                
                messages.success(request, f'Branch "{name}" created successfully!')
                return redirect('branches:list')
                
        except Exception as e:
            messages.error(request, f'Error creating branch: {str(e)}')
    
    return render(request, 'branches/branch_create.html')

@login_required
def branch_edit(request, branch_id):
    """Edit branch (admin only)"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to edit branches.')
        return redirect('reports:dashboard')
    
    branch = get_object_or_404(Branch, id=branch_id)
    
    if request.method == 'POST':
        try:
            branch.name = request.POST.get('name')
            branch.address = request.POST.get('address')
            branch.phone = request.POST.get('phone')
            branch.is_active = request.POST.get('is_active') == 'on'
            
            branch.save()
            
            messages.success(request, f'Branch "{branch.name}" updated successfully!')
            return redirect('branches:list')
            
        except Exception as e:
            messages.error(request, f'Error updating branch: {str(e)}')
    
    context = {
        'branch': branch,
    }
    
    return render(request, 'branches/branch_edit.html', context)

@login_required
def branch_delete(request, branch_id):
    """Delete branch (admin only)"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to delete branches.')
        return redirect('reports:dashboard')
    
    branch = get_object_or_404(Branch, id=branch_id)
    
    # Check if branch has data
    has_inventory = branch.inventory.exists()
    has_orders = branch.orders.exists()
    has_sales = branch.sales.exists()
    has_users = branch.users.exists()
    
    if request.method == 'POST':
        branch_name = branch.name
        branch.delete()
        messages.success(request, f'Branch "{branch_name}" deleted successfully.')
        return redirect('branches:list')
    
    context = {
        'branch': branch,
        'has_inventory': has_inventory,
        'has_orders': has_orders,
        'has_sales': has_sales,
        'has_users': has_users,
    }
    
    return render(request, 'branches/branch_delete.html', context)

@login_required
def branch_qr(request, branch_id):
    """View branch QR code"""
    if not request.user.is_manager():
        messages.error(request, 'You do not have permission to view QR codes.')
        return redirect('reports:dashboard')
    
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
    
    return render(request, 'branches/branch_qr.html', context)

@login_required
def branch_stock_view(request, branch_id):
    """View stock levels for a specific branch"""
    # Get the branch
    branch = get_object_or_404(Branch, id=branch_id)
    
    # Check permissions - only managers and admins can view other branches
    if not request.user.is_manager() and request.current_branch != branch:
        messages.error(request, 'You do not have permission to view this branch\'s inventory.')
        return redirect('inventory:dashboard')
    
    # Get filters
    search_query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    stock_status = request.GET.get('status', '')  # 'low', 'out', 'in'
    
    # Get inventory for this branch
    inventory = InventoryRecord.objects.filter(
        branch=branch
    ).select_related('sku', 'sku__category').order_by('sku__category', 'sku__name')
    
    # Apply search filter
    if search_query:
        inventory = inventory.filter(
            Q(sku__name__icontains=search_query) | 
            Q(sku__description__icontains=search_query)
        )
    
    # Apply category filter
    if category_id:
        inventory = inventory.filter(sku__category_id=category_id)
    
    # Apply stock status filter
    if stock_status == 'low':
        inventory = inventory.filter(quantity__lt=F('safety_stock'), quantity__gt=0)
    elif stock_status == 'out':
        inventory = inventory.filter(quantity=0)
    elif stock_status == 'in':
        inventory = inventory.filter(quantity__gte=F('safety_stock'))
    
    # Calculate statistics
    total_items = inventory.count()
    out_of_stock = inventory.filter(quantity=0).count()
    low_stock = inventory.filter(quantity__lt=F('safety_stock'), quantity__gt=0).count()
    in_stock = inventory.filter(quantity__gte=F('safety_stock')).count()
    
    # Calculate total value (quantity * price)
    total_value = sum(
        item.quantity * item.sku.price 
        for item in inventory
    )
    
    # Pagination
    paginator = Paginator(inventory, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all categories for filter
    categories = Category.objects.filter(is_active=True).order_by('name')
    
    # Recent transactions for this branch
    recent_txns = StockTransaction.objects.filter(
        branch=branch
    ).select_related('sku', 'user').order_by('-created_at')[:10]
    
    context = {
        'branch': branch,
        'page_obj': page_obj,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id,
        'selected_status': stock_status,
        'total_items': total_items,
        'out_of_stock': out_of_stock,
        'low_stock': low_stock,
        'in_stock': in_stock,
        'total_value': total_value,
        'recent_transactions': recent_txns,
    }
    
    return render(request, 'branches/branch_stock.html', context)