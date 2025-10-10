from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

class Branch(models.Model):
    """Restaurant branch/location"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Branches'
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def get_ordering_url(self):
        """Get the public ordering URL for this branch"""
        return f"/order/{self.code}/"

class Category(models.Model):
    """Pizza category (e.g., Classic, Premium, Specialty)"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['display_order', 'name']
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name

class SKU(models.Model):
    """Stock Keeping Unit - Pizza items"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='skus')
    price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    image = models.ImageField(upload_to='pizza/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'SKU'
        verbose_name_plural = 'SKUs'
    
    def __str__(self):
        return f"{self.name} - ₱{self.price}"

class InventoryRecord(models.Model):
    """Current stock level per branch per SKU"""
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='inventory')
    sku = models.ForeignKey(SKU, on_delete=models.CASCADE, related_name='inventory')
    quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    safety_stock = models.IntegerField(default=10, validators=[MinValueValidator(0)])
    last_restocked = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['branch', 'sku']
        ordering = ['branch', 'sku']
    
    def __str__(self):
        return f"{self.branch.code} - {self.sku.name}: {self.quantity}"
    
    def is_low_stock(self):
        """Check if stock is below safety level"""
        return self.quantity < self.safety_stock
    
    def stock_status(self):
        """Return stock status as string"""
        if self.quantity == 0:
            return "Out of Stock"
        elif self.is_low_stock():
            return "Low Stock"
        else:
            return "In Stock"

class StockTransaction(models.Model):
    """Log all stock movements"""
    TRANSACTION_TYPES = [
        ('restock', 'Restock'),
        ('sale', 'Sale'),
        ('transfer', 'Transfer'),
        ('waste', 'Waste'),
        ('adjustment', 'Adjustment'),
    ]
    
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='transactions')
    sku = models.ForeignKey(SKU, on_delete=models.CASCADE, related_name='transactions')
    quantity = models.IntegerField()  # Can be negative for deductions
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    notes = models.TextField(blank=True)
    user = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.branch.code} - {self.sku.name}: {self.quantity} ({self.transaction_type})"