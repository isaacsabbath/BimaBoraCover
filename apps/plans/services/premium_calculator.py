# For beginners: This file (apps/plans/services/premium_calculator.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

"""
Premium calculator service for insurance plans.

Pure function implementation - fully unit-testable with no external dependencies.
"""

from decimal import Decimal


# For beginners: This function 'calculate_premium' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
# For beginners: This function 'calculate_premium' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
def calculate_premium(base_rate, coverage_amount, duration_days,
                      group_size=1, payment_frequency='monthly'):
    """
    Calculate insurance premium amount.
    
    Formula:
        daily_premium = base_rate * coverage_amount * group_size
        periods = duration_days / frequency_divisor
        total_premium = daily_premium * periods
    
    Args:
        base_rate (Decimal): KES per unit coverage per day
        coverage_amount (Decimal): total coverage in KES
        duration_days (int): policy term in days
        group_size (int): number of members (default 1 for individual)
        payment_frequency (str): daily|weekly|monthly|annual
    
    Returns:
        Decimal: total premium amount in KES, rounded to 2 decimal places
    
    Raises:
        ValueError: if inputs are invalid
    
    Examples:
        >>> calculate_premium(
        ...     Decimal('0.01'),
        ...     Decimal('50000'),
        ...     30,
        ...     1,
        ...     'monthly'
        ... )
        Decimal('15000.00')
    """
    # Validate inputs
    if not isinstance(base_rate, (Decimal, int, float)):
        raise ValueError('base_rate must be a number')
    if not isinstance(coverage_amount, (Decimal, int, float)):
        raise ValueError('coverage_amount must be a number')
    if not isinstance(duration_days, int):
        raise ValueError('duration_days must be an integer')
    if not isinstance(group_size, int):
        raise ValueError('group_size must be an integer')
    
    # Convert to Decimal for precision
    base_rate = Decimal(str(base_rate))
    coverage_amount = Decimal(str(coverage_amount))
    
    if base_rate <= 0:
        raise ValueError('base_rate must be greater than 0')
    if coverage_amount <= 0:
        raise ValueError('coverage_amount must be greater than 0')
    if duration_days <= 0:
        raise ValueError('duration_days must be greater than 0')
    if group_size < 1:
        raise ValueError('group_size must be at least 1')
    
    # Calculate daily premium
    daily_premium = base_rate * coverage_amount * Decimal(group_size)
    
    # Determine period divisor based on payment frequency
    frequency_map = {
        'daily': 1,
        'weekly': 7,
        'monthly': 30,
        'annual': 365,
    }
    
    if payment_frequency not in frequency_map:
        raise ValueError(f'payment_frequency must be one of: {list(frequency_map.keys())}')
    
    frequency_divisor = frequency_map[payment_frequency]
    
    # Calculate number of periods
    periods = Decimal(duration_days) / Decimal(frequency_divisor)
    
    # Calculate total premium
    total_premium = daily_premium * periods
    
    # Round to 2 decimal places
    return round(total_premium, 2)


# For beginners: This function 'calculate_group_discount' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
# For beginners: This function 'calculate_group_discount' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
def calculate_group_discount(base_premium, group_size):
    """
    Calculate group discount (10% for 5+ members, 5% for 3-4 members).
    
    Args:
        base_premium (Decimal): Base premium before discount
        group_size (int): Number of group members
    
    Returns:
        Decimal: Discounted premium amount
    """
    base_premium = Decimal(str(base_premium))
    
    if group_size >= 5:
        discount_rate = Decimal('0.10')
    elif group_size >= 3:
        discount_rate = Decimal('0.05')
    else:
        discount_rate = Decimal('0')
    
    discount = base_premium * discount_rate
    return round(base_premium - discount, 2)
