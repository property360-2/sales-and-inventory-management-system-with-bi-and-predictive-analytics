from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid

class Order(models.Model):
    """Customer order"""
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready for Pickup'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_CHOICES = [
        ('counter', 'Pay at Counter'),
        ('gcash', 'GCash'),
        ('paymaya', 'PayMaya'),
    ]
    
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    branch = models.ForeignKey('inventory.Branch', on_delete=models.CASCADE, related_name='orders')
    customer_name = models.CharField(max_length=100, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    table_number = models.CharField(max_length=10, blank=True)
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    payment_reference = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['branch', 'status']),
            models.Index(fields=['order_number']),
        ]
    
    def __str__(self):
        return f"Order #{self.order_number} - {self.branch.code} - ₱{self.total_amount}"
    
    def save(self, *args, **kwargs):
        # Generate order number if not exists
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)
    
    def generate_order_number(self):
        """Generate unique order number"""
        from django.utils import timezone
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        random_suffix = str(uuid.uuid4().hex)[:4].upper()
        return f"{timestamp}{random_suffix}"
    
    def calculate_totals(self):
        """Calculate subtotal, tax, and total"""
        self.subtotal = sum(item.get_total() for item in self.items.all())
        self.tax = self.subtotal * Decimal('0.12')  # 12% VAT
        self.total_amount = self.subtotal + self.tax
        self.save()
    
    def can_cancel(self):
        """Check if order can be cancelled"""
        return self.status in ['pending', 'paid']
    
    def can_mark_paid(self):
        """Check if order can be marked as paid"""
        return self.status == 'pending'

class OrderItem(models.Model):
    """Items in an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    sku = models.ForeignKey('inventory.SKU', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    notes = models.CharField(max_length=200, blank=True)
    
    class Meta:
        ordering = ['id']
    
    def __str__(self):
        return f"{self.sku.name} x{self.quantity}"
    
    def get_total(self):
        """Calculate line item total"""
        return self.unit_price * self.quantity

class Payment(models.Model):
    """Payment transaction record"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference_number = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Payment gateway response
    gateway_response = models.JSONField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment #{self.reference_number} - {self.order.order_number} - ₱{self.amount}"