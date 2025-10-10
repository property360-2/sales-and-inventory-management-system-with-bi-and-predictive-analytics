from django.db.models import Sum, Avg
from django.utils import timezone
from datetime import timedelta
from .models import Forecast
from sales.models import DailySales
from inventory.models import Branch, SKU

def moving_average_forecast(data, window=7):
    """
    Calculate moving average forecast.
    
    Args:
        data: List of quantities
        window: Number of periods to average
    
    Returns:
        float: Predicted quantity
    """
    if not data or len(data) == 0:
        return 0
    
    # Use last 'window' days
    recent_data = data[-window:] if len(data) >= window else data
    
    if not recent_data:
        return 0
    
    avg = sum(recent_data) / len(recent_data)
    return max(0, round(avg))

def run_forecast():
    """
    Run demand forecast for all active SKUs in all branches.
    This should be run daily via cron job.
    """
    from django.db import transaction
    
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)
    
    # Look back 14 days for historical data
    start_date = today - timedelta(days=14)
    
    branches = Branch.objects.filter(is_active=True)
    skus = SKU.objects.filter(is_active=True)
    
    forecasts_created = 0
    
    for branch in branches:
        for sku in skus:
            try:
                # Get historical sales data
                historical_sales = DailySales.objects.filter(
                    branch=branch,
                    sku=sku,
                    date__gte=start_date,
                    date__lt=today
                ).order_by('date').values_list('total_quantity', flat=True)
                
                # Convert to list
                sales_data = list(historical_sales)
                
                # Calculate forecast
                predicted_qty = moving_average_forecast(sales_data, window=7)
                
                # Calculate confidence (simple: based on data availability)
                confidence = min(100, len(sales_data) / 7 * 100)
                
                # Create or update forecast
                with transaction.atomic():
                    forecast, created = Forecast.objects.update_or_create(
                        branch=branch,
                        sku=sku,
                        forecast_date=tomorrow,
                        defaults={
                            'predicted_quantity': predicted_qty,
                            'confidence_level': confidence,
                            'method': 'moving_average_7day'
                        }
                    )
                    
                    if created:
                        forecasts_created += 1
                        
            except Exception as e:
                print(f"Error forecasting for {branch.code} - {sku.name}: {str(e)}")
                continue
    
    print(f"Forecast completed: {forecasts_created} new forecasts created")
    return forecasts_created

def update_forecast_actuals():
    """
    Update actual quantities for past forecasts.
    Compare forecasts with actual sales.
    """
    from django.db import transaction
    
    yesterday = timezone.now().date() - timedelta(days=1)
    
    # Get forecasts that need actuals updated
    forecasts = Forecast.objects.filter(
        forecast_date=yesterday,
        actual_quantity__isnull=True
    )
    
    updated = 0
    
    for forecast in forecasts:
        try:
            # Get actual sales for that date
            daily_sale = DailySales.objects.filter(
                branch=forecast.branch,
                sku=forecast.sku,
                date=yesterday
            ).first()
            
            actual_qty = daily_sale.total_quantity if daily_sale else 0
            
            forecast.actual_quantity = actual_qty
            forecast.save()
            updated += 1
            
        except Exception as e:
            print(f"Error updating actuals for forecast {forecast.id}: {str(e)}")
            continue
    
    print(f"Updated {updated} forecast actuals")
    return updated