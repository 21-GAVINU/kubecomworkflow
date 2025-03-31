import logging
import os
import requests

LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

opa_logger = logging.getLogger("OPAIntegration")
opa_logger.setLevel(logging.INFO)

opa_log_file = os.path.join(LOG_DIR, "opa.log")
file_handler = logging.FileHandler(opa_log_file)
file_handler.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

if not opa_logger.hasHandlers():
    opa_logger.addHandler(file_handler)
else:
    opa_logger.handlers.clear()
    opa_logger.addHandler(file_handler)

OPA_URL = os.environ.get("opaServerHost", "http://localhost:8181") + "/v1/data/k8s/allow"
# OPA_URL = "http://localhost:8181/v1/data/k8s/allow" 

def opa_check_command(command: str) -> (bool, str):
    payload = {"input": {"command": command}}
    try:
        response = requests.post(OPA_URL, json=payload)
        response.raise_for_status()
        result = response.json().get("result", {})

        # Non-empty deny list = Rejection.
        deny_list = result.get("deny", [])
        allowed = result.get("allow", True) and not deny_list
        reason = "; ".join(deny_list) if deny_list else ""
        opa_logger.info(f"OPA decision '{command}': {result} | Reason: {reason}")
        return allowed, reason
    except Exception as e:
        opa_logger.error(f"Error querying OPA for command '{command}': {e}")
        return False, f"OPA query error: {e}"
