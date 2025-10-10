from django.db import models

class Forecast(models.Model):
    """Demand forecast per SKU per branch"""
    branch = models.ForeignKey('inventory.Branch', on_delete=models.CASCADE, related_name='forecasts')
    sku = models.ForeignKey('inventory.SKU', on_delete=models.CASCADE, related_name='forecasts')
    forecast_date = models.DateField()
    predicted_quantity = models.IntegerField(default=0)
    confidence_level = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # 0-100
    actual_quantity = models.IntegerField(null=True, blank=True)
    method = models.CharField(max_length=50, default='moving_average')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['branch', 'sku', 'forecast_date']
        ordering = ['-forecast_date', 'branch', 'sku']
        indexes = [
            models.Index(fields=['-forecast_date', 'branch']),
        ]
    
    def __str__(self):
        return f"{self.forecast_date} - {self.branch.code} - {self.sku.name}: {self.predicted_quantity}"
    
    def accuracy(self):
        """Calculate forecast accuracy if actual is available"""
        if self.actual_quantity is None:
            return None
        
        if self.predicted_quantity == 0 and self.actual_quantity == 0:
            return 100.0
        
        if self.predicted_quantity == 0:
            return 0.0
        
        error = abs(self.predicted_quantity - self.actual_quantity)
        accuracy = max(0, 100 - (error / self.predicted_quantity * 100))
        return round(accuracy, 2)