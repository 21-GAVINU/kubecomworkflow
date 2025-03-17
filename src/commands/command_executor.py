import subprocess
import os
import time
import re
from datetime import datetime

# Define log file path for cluster/system interactions
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "cluster_execution.log")

# Ensure logs directory exists
os.makedirs(LOG_DIR, exist_ok=True)

def log_execution(command: str, output: str, success: bool = True) -> None:
    """
    Append execution details to the log file.
    """
    status = "SUCCESS" if success else "FAILED"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] [{status}] Executed: {command}\n")
        f.write(f"{output}\n{'-' * 50}\n")

# A dictionary to store discovered resource names by type
# e.g., known_resources["services"] = {"blue-slack-service", "webapp-staging", ...}
known_resources = {
    "services": set(),
    "pods": set(),
    "deployments": set(),
    # Add more if needed
}

def parse_resource_names(command: str, output: str) -> None:
    """
    If 'command' is something like 'kubectl get svc' or 'kubectl get pods',
    parse the output to discover real resource names and store them in 'known_resources'.
    Expects the standard 'NAME' column in the output.
    """
    # Detect if this is a 'kubectl get' command for a known resource type
    # e.g. 'kubectl get svc', 'kubectl get pods', 'kubectl get deployments'
    # We'll do a simple check:
    lower_cmd = command.lower()
    if "kubectl get" in lower_cmd:
        if "svc" in lower_cmd or "services" in lower_cmd:
            resource_type = "services"
        elif "pods" in lower_cmd:
            resource_type = "pods"
        elif "deployments" in lower_cmd:
            resource_type = "deployments"
        else:
            return  # Not a resource type we track

        # Attempt to parse the NAME column from the output
        # The standard 'kubectl get' output has lines like:
        # NAME                  TYPE        CLUSTER-IP   ...
        # my-service            ClusterIP   10.105.39.202 ...
        lines = output.splitlines()
        # Find the line that starts with 'NAME' or so
        # Then parse subsequent lines' first column
        # We'll do a naive approach: skip the first line, parse the first token of each subsequent line
        if len(lines) > 1:
            for line in lines[1:]:
                parts = line.split()
                if parts:
                    resource_name = parts[0].strip()
                    known_resources[resource_type].add(resource_name)

def rewrite_command(command: str) -> str:
    """
    If the command references a resource name that isn't in known_resources but
    we have exactly one known resource of that type, we do a simple substitution.
    Example: 'kubectl describe svc my-service' => 'kubectl describe svc blue-slack-service'
    if 'my-service' is not found but we only have 'blue-slack-service' in known_resources["services"].
    """
    lower_cmd = command.lower()

    # We'll do some naive checks for resource type
    if "svc" in lower_cmd or "service" in lower_cmd:
        resource_type = "services"
    elif "pods" in lower_cmd:
        resource_type = "pods"
    elif "deployment" in lower_cmd:
        resource_type = "deployments"
    else:
        return command  # Not a resource type we handle

    # Extract the name after 'svc' or 'pods' or 'deployment' if it exists
    # This is a naive approach: we look for the first token after 'svc' or 'service'
    # Then see if it's in known_resources or not
    # If not, but known_resources has exactly one item, we rewrite
    # If multiple items or none, we skip rewriting

    # Attempt a simple regex to find 'svc <name>' or 'service <name>' or 'pods <name>' etc.
    # This is simplistic and won't catch every possible pattern
    # For example: 'kubectl describe svc my-service -n staging'
    match = re.search(r'(?:svc|service|pods|deployment)\s+([\w-]+)', command, re.IGNORECASE)
    if match:
        guessed_name = match.group(1)
        # Check if guessed_name is known
        if guessed_name not in known_resources[resource_type]:
            # If we have exactly one known resource, we might replace
            if len(known_resources[resource_type]) == 1:
                real_name = list(known_resources[resource_type])[0]
                # Replace the guessed_name with real_name in the command
                new_command = command.replace(guessed_name, real_name)
                print(f"[Rewrite] Replacing '{guessed_name}' with '{real_name}' in command: {new_command}")
                return new_command
    return command

def execute_kubectl_commands(commands, delay: int = 10) -> str:
    """
    Executes a list of kubectl commands sequentially. 
    """
    if isinstance(commands, str):
        cleaned = commands.replace("", "")
        commands = [cmd.strip() for cmd in cleaned.split(";") if cmd.strip()]
    
    aggregated_output = []

    for i, command in enumerate(commands):
        # 1) Rewrite the command if it references a placeholder
        command = rewrite_command(command)

        print(f"\nExecuting: {command}")
        # 2) Execute the command and wait for it to finish
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        success = (result.returncode == 0)
        if success:
            output = result.stdout.strip() or "Command executed successfully with no output."
        else:
            output = f"STDOUT: {result.stdout.strip()}\nSTDERR: {result.stderr.strip()}"
        # 3) Log the execution details
        log_execution(command, output, success)
        aggregated_output.append(f"Command: {command}\nOutput: {output}")
        print(output)
        # 4) Parse resource names if this was a 'kubectl get ...'
        if success:
            parse_resource_names(command, output)
        # 5) Wait between command executions
        print(f"Waiting for {delay} seconds before next command...")
        time.sleep(delay)

    return "\n\n".join(aggregated_output)