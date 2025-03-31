import subprocess
import os
import time
import re
from datetime import datetime

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "cluster_execution.log")

os.makedirs(LOG_DIR, exist_ok=True)

def log(command: str, output: str, success: bool = True) -> None:
    status = "SUCCESS" if success else "FAILED"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] [{status}] Executed: {command}\n")
        f.write(f"{output}\n{'-' * 50}\n")

known_resources = {
    "services": set(),
    "pods": set(),
    "deployments": set()
}

def parse_resource_names(command: str, output: str) -> None:

    lower_cmd = command.lower()
    if "kubectl get" in lower_cmd:
        if "svc" in lower_cmd or "services" in lower_cmd:
            resource_type = "services"
        elif "pods" in lower_cmd:
            resource_type = "pods"
        elif "deployments" in lower_cmd:
            resource_type = "deployments"
        else:
            return

        lines = output.splitlines()
        
        # Find the line that starts with 'NAME' or so
        if len(lines) > 1:
            for line in lines[1:]:
                parts = line.split()
                if parts:
                    resource_name = parts[0].strip()
                    known_resources[resource_type].add(resource_name)

def rewrite_command(command: str) -> str:
    lower_cmd = command.lower()

    if "svc" in lower_cmd or "service" in lower_cmd:
        resource_type = "services"
    elif "pods" in lower_cmd:
        resource_type = "pods"
    elif "deployment" in lower_cmd:
        resource_type = "deployments"
    else:
        return command 

    # Find 'svc <name>' or 'service <name>' or 'pods <name>' etc.
    match = re.search(r'(?:svc|service|pods|deployment)\s+([\w-]+)', command, re.IGNORECASE)
    if match:
        guessed_name = match.group(1)

        if guessed_name not in known_resources[resource_type]:
            if len(known_resources[resource_type]) == 1:
                real_name = list(known_resources[resource_type])[0]
                new_command = command.replace(guessed_name, real_name)
                print(f"[Rewrite] Replacing '{guessed_name}' with '{real_name}' in command: {new_command}")
                return new_command
    return command

def execute_kubectl_commands(commands, delay: int = 10) -> str:
    """
    Executes a sequence of kubectl commands. 
    """
    if isinstance(commands, str):
        cleaned = commands.replace("", "")
        commands = [cmd.strip() for cmd in cleaned.split(";") if cmd.strip()]
    
    aggregated_output = []

    for i, command in enumerate(commands):
        command = rewrite_command(command)

        print(f"\nExecuting: {command}")
        # Execute command
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        success = (result.returncode == 0)

        if success:
            output = result.stdout.strip() or "Command executed successfully with no output."
        else:
            output = f"STDOUT: {result.stdout.strip()}\nSTDERR: {result.stderr.strip()}"

        log(command, output, success)

        aggregated_output.append(f"Command: {command}\nOutput: {output}")
        print(output)

        if success:
            parse_resource_names(command, output)

        print(f"Waiting for {delay} seconds before next command...")
        time.sleep(delay)

    return "\n\n".join(aggregated_output)