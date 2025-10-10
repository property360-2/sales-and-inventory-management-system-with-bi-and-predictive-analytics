from .services import aggregate_sales_daily

def aggregate_sales_daily_task():
    """
    Cron job to aggregate yesterday's sales.
    Run this daily at 1 AM.
    """
    count = aggregate_sales_daily()
    print(f"Aggregated sales for {count} SKUs")
    return count