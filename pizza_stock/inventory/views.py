from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, F
from django.core.paginator import Paginator
from .models import Branch, Category, SKU, InventoryRecord, StockTransaction
from .utils import apply_stock_transaction, generate_branch_qr, get_low_stock_items
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods
from django.db import transaction
from cloudinary.uploader import upload as cloudinary_upload
from cloudinary.exceptions import Error as CloudinaryError

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
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')

    skus = SKU.objects.all().select_related('category')

    if query:
        skus = skus.filter(name__icontains=query)
    if category_id:
        skus = skus.filter(category_id=category_id)

    paginator = Paginator(skus, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'categories': Category.objects.all(),
        'page_obj': page_obj,
        'query': query,
        'selected_category': category_id,
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'inventory/partials/sku_grid.html', context)

    return render(request, 'inventory/sku_list.html', context)
@login_required
def add_sku(request):
    """Add new SKU (menu item) to the system"""
    if not request.user.is_manager():
        messages.error(request, 'You do not have permission to add menu items.')
        return redirect('inventory:sku_list')

    categories = Category.objects.filter(is_active=True)

    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            category_id = request.POST.get('category_id')
            new_category_name = request.POST.get('new_category_name', '').strip()
            price = request.POST.get('price', '0')
            image = request.FILES.get('image')  # ✅ handle image upload

            # Validation
            if not name:
                messages.error(request, 'Item name is required.')
            elif not category_id and not new_category_name:
                messages.error(request, 'Please select or create a category.')
            elif not price or float(price) <= 0:
                messages.error(request, 'Please enter a valid price.')
            else:
                # Create or get category
                if category_id == 'new' and new_category_name:
                    category, _ = Category.objects.get_or_create(
                        name=new_category_name,
                        defaults={'is_active': True}
                    )
                else:
                    category = get_object_or_404(Category, id=category_id)

                # ✅ Create SKU (with image)
                sku = SKU.objects.create(
                    name=name,
                    description=description,
                    category=category,
                    price=price,
                    image=image,
                    is_active=True
                )

                messages.success(request, f'Successfully created menu item: {sku.name}')
                return redirect('inventory:add_inventory')

        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    context = {'categories': categories}
    return render(request, 'inventory/add_sku.html', context)


@login_required
def add_inventory(request):
    """Add one or multiple SKUs to a specific branch inventory"""
    from inventory.models import SKU, InventoryRecord as Inventory, Branch

    branches = Branch.objects.filter(is_active=True)
    skus = SKU.objects.filter(is_active=True)
    categories = {sku.category for sku in skus}

    if request.method == 'POST':
        branch_id = request.POST.get('branch_id')
        notes = request.POST.get('notes', '')
        selected_skus = request.POST.getlist('selected_skus')

        if not branch_id or not selected_skus:
            messages.error(request, "Please select a branch and at least one SKU.")
            return redirect('inventory:add_inventory')

        branch = get_object_or_404(Branch, id=branch_id)

        added_count = 0
        with transaction.atomic():
            for sku_id in selected_skus:
                quantity = int(request.POST.get(f'quantity_{sku_id}', 0))
                if quantity < 0:
                    quantity = 0

                sku = get_object_or_404(SKU, id=sku_id)

                inventory, created = Inventory.objects.get_or_create(
                    branch=branch,
                    sku=sku,
                    defaults={'quantity': quantity, 'safety_stock': 10, 'notes': notes}
                )

                if not created:
                    inventory.quantity += quantity
                    inventory.save()

                added_count += 1

        messages.success(request, f"{added_count} item(s) successfully added to {branch.name}'s inventory.")
        return redirect('inventory:dashboard')

    context = {
        'branches': branches,
        'available_skus': skus,
        'categories': categories,
    }
    return render(request, 'inventory/add_inventory.html', context)

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




@login_required
@require_http_methods(["GET", "POST"])
def sku_list_api(request):
    # ✅ Handle creation via POST (AJAX form)
    if request.method == "POST":
        try:
            name = request.POST.get("name", "").strip()
            description = request.POST.get("description", "").strip()
            category_id = request.POST.get("category_id")
            new_category_name = request.POST.get("new_category_name", "").strip()
            price = request.POST.get("price", "0").strip()
            image = request.FILES.get("image")

            if not name:
                return JsonResponse({"success": False, "error": "Name is required."}, status=400)
            if not category_id and not new_category_name:
                return JsonResponse({"success": False, "error": "Category is required."}, status=400)
            if not price or float(price) <= 0:
                return JsonResponse({"success": False, "error": "Invalid price."}, status=400)

            # ✅ Handle category (existing or new)
            if category_id == "new" and new_category_name:
                category, _ = Category.objects.get_or_create(
                    name=new_category_name, defaults={"is_active": True}
                )
            else:
                category = get_object_or_404(Category, id=category_id)

            # ✅ Upload image to Cloudinary (optional)
            image_url = None
            if image:
                try:
                    upload_result = cloudinary_upload(image)
                    image_url = upload_result.get("secure_url")
                except CloudinaryError as e:
                    print("❌ Cloudinary upload failed:", e)

            # ✅ Save SKU
            with transaction.atomic():
                SKU.objects.create(
                    name=name,
                    description=description,
                    category=category,
                    price=price,
                    image=image_url,
                    is_active=True
                )

            return JsonResponse({"success": True, "message": "SKU created successfully!"})

        except Exception as e:
            print("❌ SKU creation failed:", e)
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    # ✅ Handle GET (AJAX filtering)
    query = request.GET.get("q", "")
    category_id = request.GET.get("category")
    page_number = request.GET.get("page", 1)

    skus = SKU.objects.select_related("category").all()
    if query:
        skus = skus.filter(Q(name__icontains=query) | Q(description__icontains=query))
    if category_id:
        skus = skus.filter(category_id=category_id)

    paginator = Paginator(skus, 12)
    page_obj = paginator.get_page(page_number)

    html = render_to_string("inventory/partials/sku_grid.html", {"page_obj": page_obj, "user": request.user})

    return JsonResponse({
        "html": html,
        "has_next": page_obj.has_next(),
        "has_prev": page_obj.has_previous(),
        "page": page_obj.number,
        "total_pages": paginator.num_pages,
    })