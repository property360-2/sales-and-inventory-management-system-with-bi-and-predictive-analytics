from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .models import User

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
    from inventory.models import Branch
    
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
    
    users = User.objects.all().prefetch_related('branches')
    return render(request, 'users/user_list.html', {'users': users})