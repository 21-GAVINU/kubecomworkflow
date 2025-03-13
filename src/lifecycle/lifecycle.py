import logging
import slack
from src.config.config import SLACK_BOT_TOKEN

logger = logging.getLogger(__name__)

# Initialize Slack WebClient using the token from config
web_client = slack.WebClient(token=SLACK_BOT_TOKEN)

def send_readiness_message():
    """Sends a readiness message to a designated Slack channel."""
    try:
        channel = "#kubecomworkflow"  # Update with your target channel if needed
        message = "✅ K8s Slack Bot is online!"
        web_client.chat_postMessage(channel=channel, text=message)
        logger.info("Readiness message sent.")
    except Exception as e:
        logger.error(f"Error sending readiness message: {e}")

def send_shutdown_message():
    """Sends a shutdown message to a designated Slack channel."""
    try:
        channel = "#kubecomworkflow"  # Update with your target channel if needed
        message = ":x: K8s Slack Bot is shutting down."
        web_client.chat_postMessage(channel=channel, text=message)
        logger.info("Shutdown message sent.")
    except Exception as e:
        logger.error(f"Error sending shutdown message: {e}")

def send_processing_message(channel: str, original_message: str) -> None:
    """
    Sends a processing acknowledgment message to the specified Slack channel,
    and logs the action.
    """
    try:
        message = f":hourglass_flowing_sand: Processing your message: '{original_message}'"
        web_client.chat_postMessage(channel=channel, text=message)
        logger.info(f"Processing message sent to {channel}: {message}")
    except Exception as e:
        logger.error(f"Error sending processing message: {e}")
