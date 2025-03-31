import os
from pathlib import Path
import atexit
from dotenv import load_dotenv
from src.slack.slack_handler import start_slack_bot
from src.lifecycle.lifecycle import send_readiness_message, send_shutdown_message

# Optionally, load environment variables here if not done elsewhere
# But if src/config.py is imported in slack_handler.py, it's already loaded.

# For clarity, you can force loading here:
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Print variables (for debugging)
print("signToken:", os.getenv("signToken"))
print("slackToken:", os.getenv("slackToken"))

# Start the Slack bot
if __name__ == "__main__":
    # Send the readiness message before starting the Slack bot
    send_readiness_message()
    
    # Register the shutdown message to be sent when the program exits
    atexit.register(send_shutdown_message)
    
    start_slack_bot()