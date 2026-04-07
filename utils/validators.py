"""
Utility functions for data validation and processing
"""
from typing import Optional, Dict, Any
from datetime import datetime
import re


def validate_patient_id(patient_id: str) -> bool:
    """
    Validate patient ID format
    
    Args:
        patient_id: Patient ID string
    
    Returns:
        True if valid, False otherwise
    """
    if not patient_id or len(patient_id) < 3:
        return False
    
    # Allow alphanumeric and underscores
    pattern = r'^[A-Za-z0-9_]+$'
    return bool(re.match(pattern, patient_id))


def validate_gmfcs_level(level: int) -> bool:
    """
    Validate GMFCS level (1-5)
    
    Args:
        level: GMFCS level
    
    Returns:
        True if valid, False otherwise
    """
    return 1 <= level <= 5


def validate_score(score: float, min_val: float = 0.0, max_val: float = 100.0) -> bool:
    """
    Validate score is within acceptable range
    
    Args:
        score: Score value
        min_val: Minimum acceptable value
        max_val: Maximum acceptable value
    
    Returns:
        True if valid, False otherwise
    """
    return min_val <= score <= max_val


def calculate_age(date_of_birth: datetime) -> int:
    """
    Calculate age from date of birth
    
    Args:
        date_of_birth: Date of birth
    
    Returns:
        Age in years
    """
    today = datetime.utcnow()
    age = today.year - date_of_birth.year
    
    # Adjust if birthday hasn't occurred this year
    if (today.month, today.day) < (date_of_birth.month, date_of_birth.day):
        age -= 1
    
    return age


def format_muscle_name(muscle_name: str) -> str:
    """
    Standardize muscle name format
    
    Args:
        muscle_name: Raw muscle name
    
    Returns:
        Standardized muscle name
    """
    # Convert to uppercase
    name = muscle_name.upper()
    
    # Replace common separators with underscore
    name = re.sub(r'[.\s-]+', '_', name)
    
    # Remove multiple underscores
    name = re.sub(r'_{2,}', '_', name)
    
    return name.strip('_')


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if denominator is zero
    
    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if division by zero
    
    Returns:
        Result of division or default value
    """
    if denominator == 0:
        return default
    return numerator / denominator


def clean_numeric_value(value: Any) -> Optional[float]:
    """
    Clean and convert value to float
    
    Args:
        value: Input value
    
    Returns:
        Float value or None if conversion fails
    """
    if value is None:
        return None
    
    try:
        # Remove common non-numeric characters
        if isinstance(value, str):
            value = re.sub(r'[^\d.-]', '', value)
        return float(value)
    except (ValueError, TypeError):
        return None


def generate_report_filename(patient_id: str, report_type: str, extension: str = 'pdf') -> str:
    """
    Generate standardized report filename
    
    Args:
        patient_id: Patient ID
        report_type: Type of report
        extension: File extension
    
    Returns:
        Formatted filename
    """
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    return f"{patient_id}_{report_type}_{timestamp}.{extension}"
