import sys
from loguru import logger

# Configure Logging
def configure_logging():
    # Remove default handler
    logger.remove()
    
    # Add structured handler for stdout
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        enqueue=True
    )
    
    # Optional: Add file sink for persistent logs
    logger.add(
        "logs/bob_api.log",
        rotation="10 MB",
        retention="1 week",
        level="DEBUG",
        compression="zip"
    )

# Initialize on import
configure_logging()

