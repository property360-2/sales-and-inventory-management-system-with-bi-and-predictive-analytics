# Create this file at: pizza_stock/branches/templatetags/custom_filters.py
# (You'll need to create the templatetags directory and __init__.py file)

from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiply the value by the arg"""
    try:
        return Decimal(str(value)) * Decimal(str(arg))
    except (ValueError, TypeError):
        return 0

@register.filter
def calculate_value(item):
    """Calculate inventory value (quantity * price)"""
    try:
        return item.quantity * item.sku.price
    except (AttributeError, TypeError):
        return 0