from django.contrib import admin
from .models import Forecast

@admin.register(Forecast)
class ForecastAdmin(admin.ModelAdmin):
    list_display = ['forecast_date', 'branch', 'sku', 'predicted_quantity', 'actual_quantity', 'accuracy_display', 'confidence_level']
    list_filter = ['branch', 'forecast_date']
    search_fields = ['sku__name', 'branch__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'forecast_date'
    
    def accuracy_display(self, obj):
        acc = obj.accuracy()
        if acc is None:
            return '-'
        return f"{acc}%"
    accuracy_display.short_description = 'Accuracy'