from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from inventory.models import Branch
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