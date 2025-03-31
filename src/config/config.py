BASE_MODEL_NAME = "Qwen/Qwen2.5-Coder-7B-Instruct"
ADAPTER_PATH = "/mnt/c/Users/8bit OXY/Desktop/KubecomWorkflow/model"
MAX_NEW_TOKENS = 100

from dotenv import load_dotenv
from pathlib import Path
import os

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

SIGNING_SECRET = os.environ.get("signToken")
SLACK_BOT_TOKEN = os.environ.get("slackToken")
