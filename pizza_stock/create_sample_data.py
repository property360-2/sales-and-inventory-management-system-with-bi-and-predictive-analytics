import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User
from inventory.models import Branch, Category, SKU, InventoryRecord
from inventory.utils import apply_stock_transaction, generate_branch_qr
from decimal import Decimal

print("Creating sample data...")

# Create branches
branch1, _ = Branch.objects.get_or_create(
    code='MNL01',
    defaults={
        'name': 'Manila Main Branch',
        'address': '123 Rizal Ave, Manila',
        'phone': '02-1234-5678',
        'is_active': True
    }
)

branch2, _ = Branch.objects.get_or_create(
    code='QC01',
    defaults={
        'name': 'Quezon City Branch',
        'address': '456 Commonwealth Ave, Quezon City',
        'phone': '02-8765-4321',
        'is_active': True
    }
)

print(f"✓ Created branches: {branch1.name}, {branch2.name}")

# Generate QR codes
try:
    generate_branch_qr(branch1)
    generate_branch_qr(branch2)
    print("✓ Generated QR codes for branches")
except Exception as e:
    print(f"Note: QR code generation skipped - {e}")

# Create categories
categories_data = [
    {'name': 'Classic Pizzas', 'display_order': 1},
    {'name': 'Premium Pizzas', 'display_order': 2},
    {'name': 'Specialty Pizzas', 'display_order': 3},
    {'name': 'Sides & Drinks', 'display_order': 4},
]

categories = {}
for cat_data in categories_data:
    cat, _ = Category.objects.get_or_create(
        name=cat_data['name'],
        defaults={'display_order': cat_data['display_order'], 'is_active': True}
    )
    categories[cat_data['name']] = cat

print(f"✓ Created {len(categories)} categories")

# Create SKUs
skus_data = [
    # Classic Pizzas
    {'name': 'Margherita', 'category': 'Classic Pizzas', 'price': '299.00', 'description': 'Fresh mozzarella, tomato sauce, basil'},
    {'name': 'Pepperoni', 'category': 'Classic Pizzas', 'price': '349.00', 'description': 'Classic pepperoni with mozzarella'},
    {'name': 'Hawaiian', 'category': 'Classic Pizzas', 'price': '339.00', 'description': 'Ham, pineapple, mozzarella'},
    {'name': 'Vegetarian', 'category': 'Classic Pizzas', 'price': '329.00', 'description': 'Mixed vegetables with cheese'},
    
    # Premium Pizzas
    {'name': 'Four Cheese', 'category': 'Premium Pizzas', 'price': '449.00', 'description': 'Mozzarella, parmesan, gorgonzola, ricotta'},
    {'name': 'Meat Lovers', 'category': 'Premium Pizzas', 'price': '479.00', 'description': 'Pepperoni, sausage, ham, bacon'},
    {'name': 'BBQ Chicken', 'category': 'Premium Pizzas', 'price': '429.00', 'description': 'BBQ sauce, chicken, onions, cheese'},
    
    # Specialty Pizzas
    {'name': 'Truffle Mushroom', 'category': 'Specialty Pizzas', 'price': '549.00', 'description': 'Truffle oil, mixed mushrooms, parmesan'},
    {'name': 'Seafood Delight', 'category': 'Specialty Pizzas', 'price': '599.00', 'description': 'Shrimp, squid, mussels, garlic'},
    
    # Sides & Drinks
    {'name': 'Garlic Bread', 'category': 'Sides & Drinks', 'price': '99.00', 'description': 'Toasted with garlic butter'},
    {'name': 'Chicken Wings', 'category': 'Sides & Drinks', 'price': '199.00', 'description': '6 pieces with BBQ or buffalo sauce'},
    {'name': 'Coke 1.5L', 'category': 'Sides & Drinks', 'price': '89.00', 'description': 'Coca-Cola 1.5 liter'},
]

skus = []
for sku_data in skus_data:
    sku, _ = SKU.objects.get_or_create(
        name=sku_data['name'],
        defaults={
            'category': categories[sku_data['category']],
            'price': Decimal(sku_data['price']),
            'description': sku_data['description'],
            'is_active': True
        }
    )
    skus.append(sku)

print(f"✓ Created {len(skus)} SKUs")

# Create users
admin_user, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@pizzashop.com',
        'first_name': 'Admin',
        'last_name': 'User',
        'role': 'admin',
        'is_staff': True,
        'is_superuser': True
    }
)
if created:
    admin_user.set_password('admin123')
    admin_user.save()

manager_user, created = User.objects.get_or_create(
    username='manager',
    defaults={
        'email': 'manager@pizzashop.com',
        'first_name': 'Manager',
        'last_name': 'User',
        'role': 'manager',
        'is_staff': True
    }
)
if created:
    manager_user.set_password('manager123')
    manager_user.save()

staff_user, created = User.objects.get_or_create(
    username='staff',
    defaults={
        'email': 'staff@pizzashop.com',
        'first_name': 'Staff',
        'last_name': 'User',
        'role': 'staff'
    }
)
if created:
    staff_user.set_password('staff123')
    staff_user.save()

# Assign branches to users
admin_user.branches.add(branch1, branch2)
manager_user.branches.add(branch1)
staff_user.branches.add(branch1)

print("✓ Created users: admin, manager, staff (all with password matching username + '123')")

# Create inventory for both branches
print("Creating inventory records...")
for branch in [branch1, branch2]:
    for sku in skus:
        # Random initial stock between 20-100
        import random
        initial_stock = random.randint(20, 100)
        
        inventory, _ = InventoryRecord.objects.get_or_create(
            branch=branch,
            sku=sku,
            defaults={
                'quantity': initial_stock,
                'safety_stock': 15
            }
        )
        
        # Create initial stock transaction
        apply_stock_transaction(
            branch=branch,
            sku=sku,
            qty=initial_stock,
            txn_type='restock',
            user=admin_user,
            notes='Initial stock'
        )

print(f"✓ Created inventory for {len(skus)} items across {2} branches")

print("\n" + "="*60)
print("✅ Sample data created successfully!")
print("="*60)
print("\nLogin credentials:")
print("  Admin:   username='admin'   password='admin123'")
print("  Manager: username='manager' password='manager123'")
print("  Staff:   username='staff'   password='staff123'")
print("\nBranches created:")
print(f"  - {branch1.name} (Code: {branch1.code})")
print(f"  - {branch2.name} (Code: {branch2.code})")
print("\nPublic ordering URLs:")
print(f"  - http://localhost:8000/order/{branch1.code}/")
print(f"  - http://localhost:8000/order/{branch2.code}/")
print("="*60)