import logging
from src.model.model_loader import load_model
from src.commands.command_executor import execute_kubectl_commands
from src.commands.command_generation import (
    generate_cot, 
    generate_commands_from_cot, 
    refine_commands_with_error
)
from src.opa.opa_integration import opa_check_command

# Load AI Model once
model, tokenizer = load_model()

def extract_error_from_output(execution_output: str) -> str:
    """
    Extracts error-related lines from the execution output.
    """
    lines = execution_output.split("\n")
    # Look for any line that contains 'error:' (case-insensitive)
    error_lines = [line for line in lines if "error:" in line.lower()]
    return "\n".join(error_lines) if error_lines else "Unknown error"

def process_slack_message(text):
    """
    Processes the Slack message:
      1. Generates a chain-of-thought (CoT) reasoning from the user's instruction.
      2. Uses the CoT to generate kubectl commands.
      3. Validates each command with OPA.
      4. Executes the allowed commands and returns the output.
      5. If execution fails, uses error feedback to refine the commands and re-executes them.
    """
    try:
        logging.info(f"Processing Message: {text}")

        # Stage 1: Generate Chain-of-Thought (CoT)
        cot = generate_cot(text, model, tokenizer)
        logging.info(f"Chain-of-Thought generated: {cot}")

        # Stage 2: Generate commands based on the CoT
        commands = generate_commands_from_cot(cot, model, tokenizer)
        logging.info(f"Initial Commands extracted: {commands}")

        if not commands:
            return "⚠️ No valid Kubernetes commands found."

        # Stage 3: Validate each command with OPA
        allowed_commands = []
        rejected_commands = []
        for cmd in commands:
            allowed, reason = opa_check_command(cmd)
            if allowed:
                allowed_commands.append(cmd)
            else:
                rejected_commands.append((cmd, reason))
                logging.info(f"Command rejected by OPA: {cmd} | Reason: {reason}")

        if not allowed_commands:
            # Construct a detailed error message for the user
            msg = "❌ Generated commands violate policy constraints:\n"
            for cmd, reason in rejected_commands:
                msg += f"- {cmd}: {reason}\n"
            return msg

        # Stage 4: Execute the allowed commands on the running cluster
        execution_output = execute_kubectl_commands(allowed_commands, delay=10)
        logging.info(f"Initial execution output: {execution_output}")

        # Stage 5: Check for errors and refine commands if necessary
        if "error:" in execution_output.lower():
            error_message = extract_error_from_output(execution_output)
            logging.info(f"Detected error: {error_message}")
            refined_commands = refine_commands_with_error(text, commands, error_message, model, tokenizer)
            logging.info(f"Refined Commands: {refined_commands}")
            if not refined_commands:
                return "⚠️ Unable to refine commands after error."
            refined_execution_output = execute_kubectl_commands(refined_commands, delay=10)
            logging.info(f"Refined execution output: {refined_execution_output}")
            return f"✅ Refined Execution Results:\n{refined_execution_output}"
        else:
            return f"✅ Execution Results:\n{execution_output}"

    except Exception as e:
        logging.error(f"Error processing message: {e}")
        return f"❌ Error processing request: {e}"
