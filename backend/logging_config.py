"""
Logging configuration for production
"""
import logging
import os
from datetime import datetime

# Create logs directory if it doesn't exist
LOGS_DIR = "/app/backend/logs"
os.makedirs(LOGS_DIR, exist_ok=True)

# Configure logging
def setup_logging():
    """Setup logging configuration for production"""
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # File handler for all logs
    file_handler = logging.FileHandler(
        f"{LOGS_DIR}/zenvit_crm_{datetime.now().strftime('%Y%m%d')}.log"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(detailed_formatter)
    
    # File handler for errors only
    error_handler = logging.FileHandler(
        f"{LOGS_DIR}/errors_{datetime.now().strftime('%Y%m%d')}.log"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(console_handler)
    
    # Suppress noisy loggers
    logging.getLogger("passlib").setLevel(logging.WARNING)
    logging.getLogger("motor").setLevel(logging.WARNING)
    
    return root_logger

# Performance monitoring
class PerformanceLogger:
    """Log slow queries and performance metrics"""
    
    @staticmethod
    def log_slow_query(endpoint: str, duration: float, threshold: float = 1.0):
        """Log queries that take longer than threshold"""
        if duration > threshold:
            logging.warning(
                f"SLOW QUERY: {endpoint} took {duration:.2f}s (threshold: {threshold}s)"
            )
    
    @staticmethod
    def log_api_call(method: str, endpoint: str, status_code: int, duration: float):
        """Log API call details"""
        logging.info(
            f"API: {method} {endpoint} - Status: {status_code} - Duration: {duration:.3f}s"
        )
