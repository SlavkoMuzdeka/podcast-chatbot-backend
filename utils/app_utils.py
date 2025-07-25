import logging


def setup_logger():
    """
    Setup a basic logger for the application.
    Returns a logger instance.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
    )
    return logging.getLogger(__name__)
