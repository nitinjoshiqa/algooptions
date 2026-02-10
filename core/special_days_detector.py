"""
Special Days Detector - Expiry & Macro Event Handling

Purpose:
    Detect expiry days and macro event days
    Automatically adjust position sizing, confidence, and system state
    
Architecture:
    - is_special_day(date, event_type) → bool
    - get_special_day_type(date) → str (expiry, rbi, cpi, budget, etc)
    - adjust_for_special_day(row, special_day_type) → modified_row
"""

from datetime import datetime, timedelta


class SpecialDayType:
    """Special day categories"""
    NORMAL_DAY = 'normal'
    WEEKLY_EXPIRY = 'weekly_expiry'
    MONTHLY_EXPIRY = 'monthly_expiry'
    QUARTERLY_EXPIRY = 'quarterly_expiry'
    RBI_DECISION = 'rbi_decision'
    CPI_RELEASE = 'cpi_release'
    BUDGET = 'budget'
    RBI_POLICY = 'rbi_policy'
    FPI_FLOWS = 'fpi_flows'
    EARNINGS_SEASON = 'earnings_season'
    INDEX_REBALANCE = 'index_rebalance'


def get_weekly_expiry_dates(start_date, end_date):
    """
    Get all Thursday (weekly expiry) dates in range
    India derivatives expire on Thursdays
    
    Args:
        start_date: datetime
        end_date: datetime
    
    Returns:
        list: Dates of Thursdays
    """
    dates = []
    current = start_date
    while current <= end_date:
        if current.weekday() == 3:  # Thursday = 3
            dates.append(current)
        current += timedelta(days=1)
    return dates


def get_monthly_expiry_date(year, month):
    """
    Get last Thursday of month (monthly futures expiry)
    
    Args:
        year: int
        month: int (1-12)
    
    Returns:
        datetime: Last Thursday of the month
    """
    # Find last day of month
    if month == 12:
        last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)
    
    # Backtrack to most recent Thursday
    while last_day.weekday() != 3:  # Thursday
        last_day -= timedelta(days=1)
    
    return last_day


def get_quarterly_expiry_dates(year):
    """
    Get quarterly expiry dates (last Thursday of Mar, Jun, Sep, Dec)
    
    Args:
        year: int
    
    Returns:
        list: Quarterly expiry dates
    """
    months = [3, 6, 9, 12]
    return [get_monthly_expiry_date(year, m) for m in months]


def is_expiry_day(date):
    """
    Check if date is any kind of derivatives expiry
    
    Args:
        date: datetime or date
    
    Returns:
        tuple: (is_expiry: bool, expiry_type: str)
    """
    if isinstance(date, datetime):
        date = date.date()
    
    # Monthly expiry: last Thursday
    monthly = get_monthly_expiry_date(date.year, date.month).date()
    if date == monthly:
        # Check if quarterly
        if date.month in [3, 6, 9, 12]:
            return (True, SpecialDayType.QUARTERLY_EXPIRY)
        else:
            return (True, SpecialDayType.MONTHLY_EXPIRY)
    
    # Weekly expiry: Thursday
    if date.weekday() == 3:
        return (True, SpecialDayType.WEEKLY_EXPIRY)
    
    return (False, SpecialDayType.NORMAL_DAY)


def is_macro_event_day(date):
    """
    Check if date has known macro events
    
    Note: These are approximate. Real dates vary year to year.
    For production, integrate with event_calendar.csv
    
    Args:
        date: datetime or date
    
    Returns:
        tuple: (is_event: bool, event_types: list)
    """
    if isinstance(date, datetime):
        check_date = date.date()
    else:
        check_date = date
    
    year = check_date.year
    month = check_date.month
    day = check_date.day
    
    events = []
    
    # RBI Decision (Usually 7 Feb, 7 Apr, 6 Jun, 7 Aug, 7 Oct, 6 Dec)
    rbi_decision_dates = [
        (2, 7), (4, 6), (6, 6), (8, 9), (10, 7), (12, 6)
    ]
    if any((m, d) <= (month, day) < (m, d+1) for m, d in rbi_decision_dates):
        events.append(SpecialDayType.RBI_DECISION)
    
    # CPI Release (Usually 12th of each month, 12:30 IST)
    if 10 <= day <= 14:
        events.append(SpecialDayType.CPI_RELEASE)
    
    # Budget (Usually 1st February)
    if month == 2 and 1 <= day <= 2:
        events.append(SpecialDayType.BUDGET)
    
    # RBI Policy Announcement (Around Feb, Apr, Jun, Aug, Oct, Dec)
    if month in [2, 4, 6, 8, 10, 12]:
        events.append(SpecialDayType.RBI_POLICY)
    
    # Index Rebalance (Usually 15th of every month)
    if 14 <= day <= 16:
        events.append(SpecialDayType.INDEX_REBALANCE)
    
    return (len(events) > 0, events)


def get_special_day_type(date):
    """
    Get the primary special day type for a date
    
    Args:
        date: datetime or date
    
    Returns:
        str: Special day type or 'normal'
    """
    is_expiry, expiry_type = is_expiry_day(date)
    if is_expiry:
        return expiry_type
    
    is_event, event_list = is_macro_event_day(date)
    if is_event:
        return event_list[0]  # Return most significant
    
    return SpecialDayType.NORMAL_DAY


def adjust_for_special_day(row, special_day_type):
    """
    Adjust signal parameters for special days
    
    Adjustments:
    - Weekly expiry: Confidence -20%, Position -30%
    - Monthly expiry: Confidence -30%, Position -50%, may skip
    - Quarterly expiry: May skip entirely (system_state = STAND_DOWN)
    - Macro events: Confidence -15%, Position -20%
    
    Args:
        row: Signal row dict
        special_day_type: str from get_special_day_type()
    
    Returns:
        dict: Modified row with adjustments
    """
    
    if special_day_type == SpecialDayType.NORMAL_DAY:
        return row  # No changes
    
    row = dict(row)  # Make a copy to avoid mutation
    
    # Get original values
    confidence = row.get('confidence', 70) or 70
    position_size = row.get('position_size', 1.0) or 1.0
    system_state = row.get('system_state', 'ACTIVE') or 'ACTIVE'
    
    # Base adjustments
    if special_day_type == SpecialDayType.WEEKLY_EXPIRY:
        row['confidence'] = confidence * 0.80
        row['position_size'] = position_size * 0.70
        row['special_day_flag'] = True
        row['special_day_reason'] = 'weekly_expiry_reduced_size'
    
    elif special_day_type == SpecialDayType.MONTHLY_EXPIRY:
        row['confidence'] = confidence * 0.70
        row['position_size'] = position_size * 0.50
        row['special_day_flag'] = True
        row['special_day_reason'] = 'monthly_expiry_caution'
    
    elif special_day_type == SpecialDayType.QUARTERLY_EXPIRY:
        # High volatility, avoid if possible
        row['confidence'] = confidence * 0.60
        row['position_size'] = position_size * 0.30
        row['special_day_flag'] = True
        row['special_day_reason'] = 'quarterly_expiry_minimal'
        if confidence < 85:  # Only enter if very high conviction
            row['system_state'] = 'CAUTION'
    
    elif special_day_type == SpecialDayType.RBI_DECISION:
        row['confidence'] = confidence * 0.85
        row['position_size'] = position_size * 0.80
        row['special_day_flag'] = True
        row['special_day_reason'] = 'rbi_decision_ahead'
    
    elif special_day_type == SpecialDayType.CPI_RELEASE:
        row['confidence'] = confidence * 0.85
        row['position_size'] = position_size * 0.80
        row['special_day_flag'] = True
        row['special_day_reason'] = 'cpi_release'
    
    elif special_day_type == SpecialDayType.BUDGET:
        # Budget announcement = major event
        row['confidence'] = confidence * 0.75
        row['position_size'] = position_size * 0.60
        row['special_day_flag'] = True
        row['special_day_reason'] = 'budget_announcement'
    
    elif special_day_type == SpecialDayType.INDEX_REBALANCE:
        row['confidence'] = confidence * 0.90
        row['position_size'] = position_size * 0.90
        row['special_day_flag'] = True
        row['special_day_reason'] = 'index_rebalance'
    
    else:  # Generic event
        row['confidence'] = confidence * 0.85
        row['position_size'] = position_size * 0.80
        row['special_day_flag'] = True
        row['special_day_reason'] = f'macro_event_{special_day_type}'
    
    return row
