from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

class Sale(models.Model):
    """Individual sale record"""
    branch = models.ForeignKey('inventory.Branch', on_delete=models.CASCADE, related_name='sales')
    sku = models.ForeignKey('inventory.SKU', on_delete=models.CASCADE, related_name='sales')
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    user = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['branch', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.branch.code} - {self.sku.name} x{self.quantity} - ₱{self.total_amount}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate total if not set
        if not self.total_amount:
            self.total_amount = self.unit_price * self.quantity
        super().save(*args, **kwargs)

class DailySales(models.Model):
    """Aggregated daily sales per SKU per branch"""
    branch = models.ForeignKey('inventory.Branch', on_delete=models.CASCADE, related_name='daily_sales')
    sku = models.ForeignKey('inventory.SKU', on_delete=models.CASCADE, related_name='daily_sales')
    date = models.DateField()
    total_quantity = models.PositiveIntegerField(default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    average_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    transaction_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['branch', 'sku', 'date']
        ordering = ['-date', 'branch', 'sku']
        verbose_name_plural = 'Daily sales'
        indexes = [
            models.Index(fields=['-date', 'branch']),
        ]
    
    def __str__(self):
        return f"{self.date} - {self.branch.code} - {self.sku.name}: {self.total_quantity} units"