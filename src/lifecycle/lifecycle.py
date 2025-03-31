import logging
import slack
from src.config.config import SLACK_BOT_TOKEN

logger = logging.getLogger(__name__)

web_client = slack.WebClient(token=SLACK_BOT_TOKEN)

def send_readiness_message():
    try:
        channel = "#kubecomworkflow" 
        message = "✅ K8s Slack Bot is online!"
        web_client.chat_postMessage(channel=channel, text=message)
        logger.info("Readiness message sent.")
    except Exception as e:
        logger.error(f"Error sending readiness message: {e}")

def send_shutdown_message():
    try:
        channel = "#kubecomworkflow" 
        message = ":x: K8s Slack Bot is shutting down."
        web_client.chat_postMessage(channel=channel, text=message)
        logger.info("Shutdown message sent.")
    except Exception as e:
        logger.error(f"Error sending shutdown message: {e}")

def send_processing_message(channel: str, original_message: str) -> None:
    try:
        message = f":hourglass_flowing_sand: Processing your message: '{original_message}'"
        web_client.chat_postMessage(channel=channel, text=message)
        logger.info(f"Processing message sent to {channel}: {message}")
    except Exception as e:
        logger.error(f"Error sending processing message: {e}")
