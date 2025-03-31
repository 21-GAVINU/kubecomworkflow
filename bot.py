import os
from pathlib import Path
import atexit
from dotenv import load_dotenv
from src.slack.slack_handler import start_slack_bot
from src.lifecycle.lifecycle import send_readiness_message, send_shutdown_message

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Start the Slack bot
if __name__ == "__main__":
    # Readiness Message
    send_readiness_message()
    
    # Shutdown Message
    atexit.register(send_shutdown_message)
    
    start_slack_bot()