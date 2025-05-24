import logging
from datetime import datetime
import os

# Create logs directory if it doesn't exist
logs_dir = "logs"
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Create a timestamp for the log filename - only created once when this module is imported
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = os.path.join(logs_dir, f"logs_{timestamp}.log")

def setup_logger():
    """Configure and return the root logger"""
    root_logger = logging.getLogger()
    
    # Clear any existing handlers to avoid duplicate logs
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)
    
    # Set up file handler
    file_handler = logging.FileHandler(log_filename)
    formatter = logging.Formatter('%(asctime)s - %(process)d - %(name)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s',
                                 datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    
    return root_logger

# Create and configure the logger when this module is imported
logger = setup_logger()

def get_logger(name):
    """Get a logger with the specified name that uses the same configuration"""
    return logging.getLogger(name)
