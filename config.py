import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv("secrets/.env")

# Configuration settings
API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")
