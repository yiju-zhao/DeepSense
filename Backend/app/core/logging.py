import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional

class JSONFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings after parsing the log record.
    """
    def format(self, record: logging.LogRecord) -> str:
        """
        Format the specified record as JSON.
        """
        log_record: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if available
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from the record
        if hasattr(record, "extra") and record.extra:
            log_record.update(record.extra)
        
        return json.dumps(log_record)

def setup_logging(level: int = logging.INFO) -> None:
    """
    Set up logging with the specified level.
    
    Args:
        level: The logging level to use.
    """
    # Create logger
    logger = logging.getLogger("deepsight")
    logger.setLevel(level)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Create formatter
    formatter = JSONFormatter()
    
    # Add formatter to handler
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)

# Create a logger instance
logger = logging.getLogger("deepsight")

# Set up logging with default level
setup_logging()

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: The name of the logger. If None, the root logger is returned.
        
    Returns:
        logging.Logger: The logger instance.
    """
    if name:
        return logging.getLogger(f"deepsight.{name}")
    return logger