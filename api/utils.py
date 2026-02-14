
import calendar
import re
from typing import Optional


def extract_date_range(query: str, default_year: int = 2025) -> Optional[tuple[str, str]]:
    """
    Extract a date range from a natural language query.
    Returns (start_date, end_date) as YYYY-MM-DD strings, or None.

    Supported formats:
    - YYYY-MM-DD (specific day)
    - "June 2025" -> 2025-06-01 to 2025-06-30
    - "June" -> default_year-06-01 to default_year-06-30
    """
    q = query.lower()

    # 1. YYYY-MM-DD
    match_full = re.search(r'(\d{4})-(\d{2})-(\d{2})', q)
    if match_full:
        d = match_full.group(0)
        return (d, d)

    # 2. Month Year (e.g., "june 2025") or just Month ("june")
    months = {
        "january": 1, "jan": 1,
        "february": 2, "feb": 2,
        "march": 3, "mar": 3,
        "april": 4, "apr": 4,
        "may": 5,
        "june": 6, "jun": 6,
        "july": 7, "jul": 7,
        "august": 8, "aug": 8,
        "september": 9, "sep": 9, "sept": 9,
        "october": 10, "oct": 10,
        "november": 11, "nov": 11,
        "december": 12, "dec": 12
    }


    # Regex: Word boundary, month name, optional space+year, word boundary
    month_names = '|'.join(months.keys())
    pattern = r'\b(' + month_names + r')(?:\s+(\d{4}))?\b'
    match = re.search(pattern, q)

    if match:
        month_str = match.group(1)
        year_str = match.group(2)

        month = months[month_str]
        year = int(year_str) if year_str else default_year

        last_day = calendar.monthrange(year, month)[1]
        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month:02d}-{last_day:02d}"

        return (start_date, end_date)

    # 3. Year only (e.g. "in 2024", "year 2024")
    # Must use preposition to avoid matching random numbers like "Found 2024 messages"
    match_year = re.search(r'\b(?:in|year|of)\s+(\d{4})\b', q)
    if match_year:
        year = int(match_year.group(1))
        # Basic sanity check (1900-2100)
        if 1900 <= year <= 2100:
             return (f"{year}-01-01", f"{year}-12-31")

    return None
