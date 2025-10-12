from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db import transaction
from .models import User
from inventory.models import Branch

@require_http_methods(["GET", "POST"])
def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('reports:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            next_url = request.GET.get('next', 'reports:dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'users/login.html')

@login_required
def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('users:login')

@login_required
def profile_view(request):
    """Display user profile"""
    return render(request, 'users/profile.html', {
        'user': request.user,
        'branches': request.user.branches.all()
    })

@login_required
def switch_branch(request, branch_id):
    """Switch current active branch"""
    try:
        branch = Branch.objects.get(id=branch_id)
        if request.user.can_access_branch(branch):
            request.session['current_branch_id'] = branch_id
            messages.success(request, f'Switched to {branch.name}')
        else:
            messages.error(request, 'You do not have access to this branch.')
    except Branch.DoesNotExist:
        messages.error(request, 'Branch not found.')
    
    return redirect(request.META.get('HTTP_REFERER', 'reports:dashboard'))

@login_required
def user_list(request):
    """List all users (admin only)"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('reports:dashboard')
    
    users = User.objects.all().prefetch_related('branches').order_by('-date_joined')
    
    context = {
        'users': users,
        'total_users': users.count(),
        'admin_count': users.filter(role='admin').count(),
        'manager_count': users.filter(role='manager').count(),
        'staff_count': users.filter(role='staff').count(),
    }
    
    return render(request, 'users/user_list.html', context)

@login_required
def user_create(request):
    """Create new user (admin only)"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to create users.')
        return redirect('reports:dashboard')
    
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            email = request.POST.get('email')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')
            role = request.POST.get('role')
            phone = request.POST.get('phone')
            branch_ids = request.POST.getlist('branches')
            is_active = request.POST.get('is_active') == 'on'
            
            # Validation
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists.')
                return redirect('users:user_create')
            
            if password != password_confirm:
                messages.error(request, 'Passwords do not match.')
                return redirect('users:user_create')
            
            if len(password) < 8:
                messages.error(request, 'Password must be at least 8 characters.')
                return redirect('users:user_create')
            
            # Create user
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    role=role,
                    phone=phone,
                    is_active=is_active,
                    is_staff=role in ['admin', 'manager']
                )
                
                # Assign branches
                if branch_ids:
                    branches = Branch.objects.filter(id__in=branch_ids)
                    user.branches.set(branches)
                
                messages.success(request, f'User {username} created successfully!')
                return redirect('users:user_list')
                
        except Exception as e:
            messages.error(request, f'Error creating user: {str(e)}')
    
    branches = Branch.objects.filter(is_active=True)
    
    context = {
        'branches': branches,
    }
    
    return render(request, 'users/user_create.html', context)

@login_required
def user_edit(request, user_id):
    """Edit user (admin only)"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to edit users.')
        return redirect('reports:dashboard')
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        try:
            user.email = request.POST.get('email')
            user.first_name = request.POST.get('first_name')
            user.last_name = request.POST.get('last_name')
            user.role = request.POST.get('role')
            user.phone = request.POST.get('phone')
            user.is_active = request.POST.get('is_active') == 'on'
            user.is_staff = user.role in ['admin', 'manager']
            
            # Update password if provided
            new_password = request.POST.get('new_password')
            if new_password:
                password_confirm = request.POST.get('password_confirm')
                if new_password != password_confirm:
                    messages.error(request, 'Passwords do not match.')
                    return redirect('users:user_edit', user_id=user_id)
                if len(new_password) < 8:
                    messages.error(request, 'Password must be at least 8 characters.')
                    return redirect('users:user_edit', user_id=user_id)
                user.set_password(new_password)
            
            user.save()
            
            # Update branches
            branch_ids = request.POST.getlist('branches')
            if branch_ids:
                branches = Branch.objects.filter(id__in=branch_ids)
                user.branches.set(branches)
            else:
                user.branches.clear()
            
            messages.success(request, f'User {user.username} updated successfully!')
            return redirect('users:user_list')
            
        except Exception as e:
            messages.error(request, f'Error updating user: {str(e)}')
    
    branches = Branch.objects.filter(is_active=True)
    
    context = {
        'edit_user': user,
        'branches': branches,
    }
    
    return render(request, 'users/user_edit.html', context)

@login_required
def user_delete(request, user_id):
    """Delete user (admin only)"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to delete users.')
        return redirect('reports:dashboard')
    
    user = get_object_or_404(User, id=user_id)
    
    # Prevent deleting yourself
    if user.id == request.user.id:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('users:user_list')
    
    # Prevent deleting superusers
    if user.is_superuser:
        messages.error(request, 'Cannot delete superuser accounts.')
        return redirect('users:user_list')
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted successfully.')
        return redirect('users:user_list')
    
    context = {
        'delete_user': user,
    }
    
    return render(request, 'users/user_delete.html', context)