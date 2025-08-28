import logging

from config import MyConfig


def setup_logging(config: MyConfig):
    """Setup application logging"""

    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully")
