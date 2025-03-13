import logging
import os
import requests

# Ensure the logs directory exists
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Set up a dedicated logger for OPA integration
opa_logger = logging.getLogger("OPAIntegration")
opa_logger.setLevel(logging.INFO)

# Create a file handler that writes to logs/opa.log
opa_log_file = os.path.join(LOG_DIR, "opa.log")
file_handler = logging.FileHandler(opa_log_file)
file_handler.setLevel(logging.INFO)

# Define the log format and set it to the file handler
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

# Add the file handler to the OPA logger if it's not already added
if not opa_logger.hasHandlers():
    opa_logger.addHandler(file_handler)
else:
    # Clear existing handlers and add our file handler
    opa_logger.handlers.clear()
    opa_logger.addHandler(file_handler)

OPA_URL = "http://localhost:8181/v1/data/k8s/allow"

def opa_check_command(command: str) -> (bool, str):
    """
    Sends the command to the OPA server for evaluation.
    
    :param command: The generated kubectl command.
    :return: A tuple (allowed, reason) where allowed is True if the command is allowed,
             and reason is a string with the deny message if any.
    """
    payload = {"input": {"command": command}}
    try:
        response = requests.post(OPA_URL, json=payload)
        response.raise_for_status()
        result = response.json().get("result", {})
        # Treat any non-empty deny list as a rejection.
        deny_list = result.get("deny", [])
        allowed = result.get("allow", True) and not deny_list
        reason = "; ".join(deny_list) if deny_list else ""
        opa_logger.info(f"OPA decision for command '{command}': {result} | Reason: {reason}")
        return allowed, reason
    except Exception as e:
        opa_logger.error(f"Error querying OPA for command '{command}': {e}")
        return False, f"OPA query error: {e}"
