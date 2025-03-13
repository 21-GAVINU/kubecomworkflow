import logging
import os

# Define the log file path (you can adjust the path as needed)
LOG_FILE_PATH = r"/mnt/c/Users/8bit OXY/Desktop/KubecomWorkflow/logs/bot.log"

# Configure logging: set level, format, and handlers
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE_PATH),
        logging.StreamHandler()
    ]
)

# Create and export a logger instance
logger = logging.getLogger(__name__)
