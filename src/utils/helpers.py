"""
Helper utilities for the assessment toolkit.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def format_bytes(bytes_value: int, precision: int = 2) -> str:
    """
    Format bytes into human-readable string.
    
    Args:
        bytes_value: Number of bytes
        precision: Decimal precision
        
    Returns:
        Formatted string (e.g., "1.23 GB")
    """
    if bytes_value == 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    unit_index = 0
    value = float(bytes_value)
    
    while value >= 1024 and unit_index < len(units) - 1:
        value /= 1024
        unit_index += 1
    
    return f"{value:.{precision}f} {units[unit_index]}"


def format_currency(amount: float, currency: str = "USD") -> str:
    """
    Format currency value.
    
    Args:
        amount: Currency amount
        currency: Currency code
        
    Returns:
        Formatted currency string
    """
    return f"${amount:,.2f}"


def sanitize_resource_id(resource_id: str) -> str:
    """
    Sanitize Azure resource ID for public reports.
    
    Args:
        resource_id: Full Azure resource ID
        
    Returns:
        Sanitized resource ID with subscription/resource group masked
    """
    # Replace subscription ID with placeholder
    resource_id = re.sub(
        r'/subscriptions/[a-f0-9-]+',
        '/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
        resource_id,
        flags=re.IGNORECASE
    )
    
    # Optionally mask resource group
    resource_id = re.sub(
        r'/resourceGroups/[^/]+',
        '/resourceGroups/rg-***',
        resource_id,
        flags=re.IGNORECASE
    )
    
    return resource_id


def parse_resource_id(resource_id: str) -> Dict[str, str]:
    """
    Parse Azure resource ID into components.
    
    Args:
        resource_id: Azure resource ID
        
    Returns:
        Dictionary with parsed components
    """
    parts = {
        'subscription_id': None,
        'resource_group': None,
        'provider': None,
        'resource_type': None,
        'resource_name': None
    }
    
    pattern = r'/subscriptions/(?P<subscription>[^/]+)/resourceGroups/(?P<resource_group>[^/]+)/providers/(?P<provider>[^/]+)/(?P<resource_type>[^/]+)/(?P<resource_name>[^/]+)'
    match = re.match(pattern, resource_id, re.IGNORECASE)
    
    if match:
        parts['subscription_id'] = match.group('subscription')
        parts['resource_group'] = match.group('resource_group')
        parts['provider'] = match.group('provider')
        parts['resource_type'] = match.group('resource_type')
        parts['resource_name'] = match.group('resource_name')
    
    return parts


def calculate_days_since(date_value: datetime) -> int:
    """
    Calculate days since a given date.
    
    Args:
        date_value: Date to calculate from
        
    Returns:
        Number of days since the date
    """
    if not date_value:
        return 0
    
    # Ensure timezone-aware comparison
    if date_value.tzinfo is None:
        date_value = date_value.replace(tzinfo=timezone.utc)
    
    now = datetime.now(timezone.utc)
    delta = now - date_value
    
    return delta.days


def ensure_directory(directory: str) -> Path:
    """
    Ensure directory exists, create if it doesn't.
    
    Args:
        directory: Directory path
        
    Returns:
        Path object
    """
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Ensured directory exists: {path}")
    return path


def get_timestamp_string() -> str:
    """
    Get current timestamp as formatted string.
    
    Returns:
        Timestamp string (YYYY-MM-DD_HH-MM-SS)
    """
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def calculate_percentage(part: float, whole: float) -> float:
    """
    Calculate percentage safely.
    
    Args:
        part: Part value
        whole: Whole value
        
    Returns:
        Percentage (0-100)
    """
    if whole == 0:
        return 0.0
    return (part / whole) * 100


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate string to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def validate_naming_convention(name: str, pattern: str) -> bool:
    """
    Validate resource name against naming convention pattern.
    
    Args:
        name: Resource name
        pattern: Regex pattern
        
    Returns:
        True if name matches pattern
    """
    if not pattern:
        return True
    
    try:
        return bool(re.match(pattern, name))
    except re.error as e:
        logger.warning(f"Invalid regex pattern: {e}")
        return True


def flatten_dict(data: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """
    Flatten nested dictionary.
    
    Args:
        data: Dictionary to flatten
        parent_key: Parent key prefix
        sep: Separator between keys
        
    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in data.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def setup_logging(verbose: bool = False) -> None:
    """
    Setup logging configuration.
    
    Args:
        verbose: Enable verbose (DEBUG) logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Reduce Azure SDK logging noise
    logging.getLogger('azure').setLevel(logging.WARNING)
    logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
