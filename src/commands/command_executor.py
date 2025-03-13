
import subprocess
import os
import time
from datetime import datetime

# Define log file path for cluster/system interactions
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "cluster_execution.log")

# Ensure logs directory exists
os.makedirs(LOG_DIR, exist_ok=True)

def log_execution(command: str, output: str, success: bool = True) -> None:
    """
    Append execution details to the log file.
    
    :param command: The kubectl command executed.
    :param output: The output (stdout and/or stderr) of the command.
    :param success: Boolean indicating if the command succeeded.
    """
    status = "SUCCESS" if success else "FAILED"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] [{status}] Executed: {command}\n")
        f.write(f"{output}\n{'-' * 50}\n")

def execute_kubectl_commands(commands, delay: int = 10) -> str:
    """
    Executes a list of kubectl commands sequentially. 
    
    Each command is executed with shell=True and the function waits for it to complete
    before moving to the next command. A delay (in seconds) is introduced between each
    command to allow resources (like Pods or namespaces) time to spin up.
    
    :param commands: A list of command strings to execute.
                     Alternatively, if a single string is provided with commands separated by semicolons,
                     it will be split.
    :param delay: Number of seconds to wait between commands (default: 10 seconds).
    :return: Aggregated output of all commands.
    """
    # If commands is a string, remove any code block markers and split on semicolons
    if isinstance(commands, str):
        # Remove backticks or any code block markers
        cleaned = commands.replace("", "")
        commands = [cmd.strip() for cmd in cleaned.split(";") if cmd.strip()]
    
    aggregated_output = []

    for command in commands:
        try:
            print(f"\nExecuting: {command}")
            # Execute the command and wait for it to finish
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            success = result.returncode == 0
            if success:
                output = result.stdout.strip() or "Command executed successfully with no output."
            else:
                output = f"STDOUT: {result.stdout.strip()}\nSTDERR: {result.stderr.strip()}"
            # Log the execution details
            log_execution(command, output, success)
            aggregated_output.append(f"Command: {command}\nOutput: {output}")
            print(output)
            # Wait between command executions
            print(f"Waiting for {delay} seconds before next command...")
            time.sleep(delay)
        except Exception as e:
            error_msg = f"Error executing command: {command}\n{e}"
            print(error_msg)
            log_execution(command, error_msg, success=False)
            aggregated_output.append(error_msg)

    return "\n\n".join(aggregated_output)