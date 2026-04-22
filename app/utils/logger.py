"""
Application logging utility.
Creates and maintains log files with categorized messages (error, warning, information).
Logs are stored in separate files by category for easy management.
"""
import os
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Log directory - create if it doesn't exist
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# Log file paths
ERROR_LOG_FILE = os.path.join(LOG_DIR, 'error.log')
WARNING_LOG_FILE = os.path.join(LOG_DIR, 'warning.log')
INFO_LOG_FILE = os.path.join(LOG_DIR, 'info.log')

# Configure loggers for different categories
def setup_logger(name, log_file, level=logging.INFO):
    """
    Setup a logger with file handler.
    
    Args:
        name: Logger name
        log_file: Path to log file
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create file handler with rotation (10MB max, keep 5 backups)
    handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    handler.setLevel(level)
    
    # Create formatter with timestamp, level, and message
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    return logger

# Initialize loggers for each category
error_logger = setup_logger('error_logger', ERROR_LOG_FILE, logging.ERROR)
warning_logger = setup_logger('warning_logger', WARNING_LOG_FILE, logging.WARNING)
info_logger = setup_logger('info_logger', INFO_LOG_FILE, logging.INFO)

def log_error(message, user_id=None, additional_info=None):
    """
    Log an error message.
    
    Args:
        message: Error message to log
        user_id: Optional user ID associated with the error
        additional_info: Optional additional context information
    """
    log_entry = message
    if user_id:
        log_entry = f"User ID: {user_id} - {log_entry}"
    if additional_info:
        log_entry = f"{log_entry} | Additional Info: {additional_info}"
    error_logger.error(log_entry)

def log_warning(message, user_id=None, additional_info=None):
    """
    Log a warning message.
    
    Args:
        message: Warning message to log
        user_id: Optional user ID associated with the warning
        additional_info: Optional additional context information
    """
    log_entry = message
    if user_id:
        log_entry = f"User ID: {user_id} - {log_entry}"
    if additional_info:
        log_entry = f"{log_entry} | Additional Info: {additional_info}"
    warning_logger.warning(log_entry)

def log_info(message, user_id=None, additional_info=None):
    """
    Log an information message.
    
    Args:
        message: Information message to log
        user_id: Optional user ID associated with the info
        additional_info: Optional additional context information
    """
    log_entry = message
    if user_id:
        log_entry = f"User ID: {user_id} - {log_entry}"
    if additional_info:
        log_entry = f"{log_entry} | Additional Info: {additional_info}"
    info_logger.info(log_entry)

def read_log_file(log_type='info', lines=100):
    """
    Read log entries from a specific log file.
    
    Args:
        log_type: Type of log to read ('error', 'warning', 'info')
        lines: Number of lines to read from the end (default: 100)
        
    Returns:
        List of log entries (most recent first)
    """
    log_file_map = {
        'error': ERROR_LOG_FILE,
        'warning': WARNING_LOG_FILE,
        'info': INFO_LOG_FILE
    }
    
    log_file = log_file_map.get(log_type.lower(), INFO_LOG_FILE)
    
    if not os.path.exists(log_file):
        return []
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            # Return last N lines, most recent first
            return list(reversed(all_lines[-lines:])) if all_lines else []
    except Exception as e:
        # If reading fails, log it and return empty list
        error_logger.error(f"Failed to read log file {log_file}: {str(e)}")
        return []

def get_log_stats():
    """
    Get statistics about log files.
    
    Returns:
        Dictionary with log file statistics
    """
    stats = {}
    log_files = {
        'error': ERROR_LOG_FILE,
        'warning': WARNING_LOG_FILE,
        'info': INFO_LOG_FILE
    }
    
    for log_type, log_file in log_files.items():
        if os.path.exists(log_file):
            file_size = os.path.getsize(log_file)
            # Count lines in file
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    line_count = sum(1 for _ in f)
            except:
                line_count = 0
            
            stats[log_type] = {
                'size': file_size,
                'lines': line_count,
                'last_modified': datetime.fromtimestamp(os.path.getmtime(log_file)).strftime('%Y-%m-%d %H:%M:%S') if file_size > 0 else 'Never'
            }
        else:
            stats[log_type] = {
                'size': 0,
                'lines': 0,
                'last_modified': 'Never'
            }
    
    return stats

