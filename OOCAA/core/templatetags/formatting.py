from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter(name="sci_notation")
def sci_notation(value, precision=1):
    """Format a numeric value in scientific notation.

    Example: 1.2e-22
    """
    if value is None:
        return ""
    try:
        precision = int(precision)
    except (TypeError, ValueError):
        precision = 1

    try:
        if isinstance(value, Decimal):
            value = float(value)
        return f"{value:.{precision}e}"
    except (TypeError, ValueError, InvalidOperation):
        return value
