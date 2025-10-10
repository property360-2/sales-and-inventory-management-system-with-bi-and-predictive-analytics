from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg
from datetime import timedelta
from django.utils import timezone
from .models import Forecast

@login_required
def forecast_dashboard(request):
    """Forecast overview"""
    if not request.user.is_manager():
        messages.error(request, 'You do not have permission to view forecasts.')
        return redirect('reports:dashboard')
    
    branch = request.current_branch
    
    if not branch:
        messages.warning(request, 'Please select a branch.')
        return redirect('users:profile')
    
    # Get tomorrow's forecast
    tomorrow = timezone.now().date() + timedelta(days=1)
    
    forecasts = Forecast.objects.filter(
        branch=branch,
        forecast_date=tomorrow
    ).select_related('sku', 'sku__category').order_by('-predicted_quantity')
    
    # Get recent forecast accuracy
    recent_forecasts = Forecast.objects.filter(
        branch=branch,
        actual_quantity__isnull=False
    ).order_by('-forecast_date')[:30]
    
    # Calculate average accuracy
    accuracies = [f.accuracy() for f in recent_forecasts if f.accuracy() is not None]
    avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0
    
    context = {
        'forecasts': forecasts,
        'recent_forecasts': recent_forecasts[:10],
        'avg_accuracy': round(avg_accuracy, 2),
        'forecast_date': tomorrow,
    }
    
    return render(request, 'forecast/dashboard.html', context)