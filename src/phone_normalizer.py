"""Phone number normalizer module for Egyptian phone numbers.

This module normalises phone numbers to Egyptian local format
(starting with 0) and flags suspicious/invalid numbers with a? suffix.
"""

import re
import logging

logger = logging.getLogger(__name__)


def is_valid_phone(number):
    """Check if number length is within valid range."""
    return len(number) in [10, 11, 12, 13, 14, 15]


def normalize_phone(number: str) -> str:
    """Normalize a phone number to Egyptian local format.

    Args:
        number: Raw phone number string (may contain spaces, dashes, etc.)

    Returns:
        str: Normalised phone number in local format (starting with 0),
            or original + "?" if invalid

    Examples:
        "01012345678" → "01012345678"
        "201012345678" → "01012345678"
        "+201012345678" → "01012345678"
        "010 1234 5678" → "01012345678"
        "" → "?"
        None → "?"
        "12345" → "12345?"
    """
    if number is None or number == "":
        return "?"

    number = re.sub(r"[\s\-\(\)]+", "", str(number))
    number = number.lstrip("+")

    if not is_valid_phone(number):
        return f"{number}?"

    try:
        if len(number) == 10:
            raise ValueError("10-digit number is invalid")

        elif len(number) == 11:
            if number.startswith("0"):
                return number
            else:
                raise ValueError("Invalid 11-digit number format")

        elif len(number) == 12:
            normalized = number[1:]
            if normalized.startswith("0"):
                return normalized
            else:
                raise ValueError("12-digit number invalid after removing first digit")

        elif len(number) == 13:
            normalized = number[2:]
            if normalized.startswith("0"):
                return normalized
            elif number.startswith("2") and number.endswith("0"):
                normalized = number[1:-1]
                if normalized.startswith("0"):
                    return normalized
                else:
                    raise ValueError("13-digit number invalid after fallback removal")
            else:
                raise ValueError("Invalid 13-digit number format")

        elif len(number) == 14:
            if number.startswith("2") and number.endswith("0"):
                normalized = number[2:-1]
                if normalized.startswith("0"):
                    return normalized
                else:
                    raise ValueError(
                        "14-digit number invalid after removing first 2 digits"
                    )
            else:
                raise ValueError("Invalid 14-digit number format")

        elif len(number) == 15:
            raise ValueError("15-digit number is invalid")

        else:
            raise ValueError("Unexpected number length")

    except ValueError as e:
        logger.warning(f"Phone normalization error for '{number}': {e}")
        return f"{number}?"


def normalize_phones(df):
    """Normalize all phone numbers in a DataFrame.

    Args:
        df: DataFrame with a "PhoneNumber" column

    Returns:
        DataFrame: Same DataFrame with normalized PhoneNumber column

    Side effects:
        Logs WARNING if any phones are flagged with ?
    """
    df["PhoneNumber"] = df["PhoneNumber"].apply(normalize_phone)

    flagged = df["PhoneNumber"].str.contains("?", regex=False, na=False).sum()
    if flagged > 0:
        logger.warning(f"Phone issues (flagged with ?): {flagged}")

    return df
