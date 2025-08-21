import os
import logging

from config import MyConfig
from logging.handlers import RotatingFileHandler


def setup_logging(config: MyConfig):
    """Setup application logging"""

    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(config.LOG_FILE_PATH)
    os.makedirs(log_dir, exist_ok=True)

    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),  # Console output
            RotatingFileHandler(
                config.LOG_FILE_PATH, maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
            ),
        ],
    )

    # Set specific log levels for different modules
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully")
