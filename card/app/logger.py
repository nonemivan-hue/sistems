"""
Logging module for Transport Cards Accounting System.
Logs all user actions and system events to a file for debugging and auditing.
"""
import os
import logging
from datetime import datetime
from pathlib import Path

# Log directory - same level as data folder
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Log file path with date
LOG_FILE = LOG_DIR / f"app_{datetime.now().strftime('%Y%m%d')}.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()  # Also output to console
    ]
)

logger = logging.getLogger(__name__)


def log_user_action(user_id: str, action: str, details: str = "", ip_address: str = ""):
    """
    Log a user action to the log file.
    
    Args:
        user_id: User ID who performed the action
        action: Action type (LOGIN, LOGOUT, CREATE_CARD, etc.)
        details: Additional details about the action
        ip_address: IP address of the client (optional)
    """
    logger.info(f"USER_ACTION | user_id={user_id} | action={action} | details={details} | ip={ip_address}")


def log_system_event(event_type: str, message: str, extra_data: dict = None):
    """
    Log a system event (database operations, errors, etc.).
    
    Args:
        event_type: Type of system event (DB_QUERY, ERROR, WARNING, etc.)
        message: Event message
        extra_data: Additional data as dictionary (optional)
    """
    if extra_data:
        extra_str = " | ".join(f"{k}={v}" for k, v in extra_data.items())
        logger.info(f"SYSTEM_EVENT | type={event_type} | {message} | {extra_str}")
    else:
        logger.info(f"SYSTEM_EVENT | type={event_type} | {message}")


def log_db_query(table: str, operation: str, duration_ms: float = None, error: str = None):
    """
    Log a database query/operation for performance monitoring.
    
    Args:
        table: Table name
        operation: Operation type (SELECT, INSERT, UPDATE, DELETE)
        duration_ms: Query execution time in milliseconds (optional)
        error: Error message if operation failed (optional)
    """
    if error:
        logger.error(f"DB_OPERATION | table={table} | op={operation} | ERROR={error}")
    elif duration_ms is not None:
        logger.info(f"DB_OPERATION | table={table} | op={operation} | duration={duration_ms:.2f}ms")
    else:
        logger.info(f"DB_OPERATION | table={table} | op={operation}")


def log_performance_metric(metric_name: str, value: float, unit: str = "ms"):
    """
    Log a performance metric.
    
    Args:
        metric_name: Name of the metric
        value: Metric value
        unit: Unit of measurement (default: ms)
    """
    logger.info(f"PERFORMANCE | metric={metric_name} | value={value}{unit}")


def log_error(error: Exception, context: str = "", extra_data: dict = None):
    """
    Log an error with stack trace.
    
    Args:
        error: Exception object
        context: Context where the error occurred
        extra_data: Additional data (optional)
    """
    if extra_data:
        extra_str = " | ".join(f"{k}={v}" for k, v in extra_data.items())
        logger.error(f"ERROR | context={context} | {str(error)} | {extra_str}", exc_info=True)
    else:
        logger.error(f"ERROR | context={context} | {str(error)}", exc_info=True)


def log_warning(message: str, context: str = ""):
    """
    Log a warning message.
    
    Args:
        message: Warning message
        context: Context where the warning occurred
    """
    logger.warning(f"WARNING | context={context} | {message}")


def get_log_file_path() -> str:
    """Return the current log file path."""
    return str(LOG_FILE)


def get_all_logs() -> list:
    """
    Get all log files sorted by date (newest first).
    
    Returns:
        List of log file paths
    """
    if not LOG_DIR.exists():
        return []
    
    log_files = list(LOG_DIR.glob("app_*.log"))
    log_files.sort(reverse=True)
    return [str(f) for f in log_files]
