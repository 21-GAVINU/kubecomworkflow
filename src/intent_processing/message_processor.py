import logging
import re
from src.model.model_loader import load_model
from src.commands.command_executor import execute_kubectl_commands
from src.commands.command_generation import (
    generate_cot, 
    generate_commands, 
    refine_commands
)
from src.opa.opa_integration import opa_check_command

model, tokenizer = load_model()

def extract_error_from_output(execution_output: str) -> str:
    lines = execution_output.split("\n")
    error_lines = [line for line in lines if "error:" in line.lower()]
    return "\n".join(error_lines) if error_lines else "Unknown error"

def extract_steps_from_cot(cot: str) -> str:
    """
    Extracts only the bullet-pointed or numbered steps from the full chain-of-thought.
    If no steps are found, returns the entire CoT.
    """
    lines = cot.splitlines()
    bullet_lines = []
    for line in lines:
        stripped = line.strip()
        # Skip lines that match a generic placeholder"
        if re.match(r"^step\s*\d+:\s*<.*?>\s*$", stripped, re.IGNORECASE):
            continue
        # If line starts with a dash, a digit+period, or "Step X:" treat it as a step
        if (stripped.startswith("-")
            or re.match(r"^\d+\.", stripped)
            or re.match(r"^step\s*\d+:", stripped, re.IGNORECASE)):
            bullet_lines.append(stripped)
    if bullet_lines:
        return "\n".join(bullet_lines)
    # Fallback: return entire chain-of-thought if no bullet lines found
    return cot

def process_slack_message(text):
    """
    Generator function that processes the Slack message in stages,
    yielding live feedback:
      - Stage 'cot': The Chain-of-Thought reasoning (only the 'steps').
      - Stage 'commands': The validated (and auto-corrected) Kubernetes commands.
      - Stage 'final': The final execution result.
    If refinement occurs, it yields an additional 'refined' stage.
    """
    try:
        logging.info(f"Processing Message: {text}")

        # Stage 1: Generate Chain-of-Thought (CoT)
        cot = generate_cot(text, model, tokenizer)
        logging.info(f"Chain-of-Thought generated: {cot}")
        
        # Extract only the "steps" portion from the CoT
        steps_only = extract_steps_from_cot(cot)

        # Yield the steps instead of the entire CoT
        yield {"stage": "cot", "message": f"💡 *Chain-of-Thought:*\n```{steps_only}```"}

        # Stage 2: Generate commands based on the CoT
        commands = generate_commands(cot, model, tokenizer)
        logging.info(f"Initial Commands extracted: {commands}")
        if not commands:
            yield {"stage": "final", "message": "⚠️ No valid Kubernetes commands found."}
            return

        # Stage 3: Validate each command with OPA
        allowed_commands = []
        rejected_commands = []
        for cmd in commands:
            allowed, reason = opa_check_command(cmd)
            if allowed:
                allowed_commands.append(cmd)
            else:
                if "no namespace provided" in reason.lower():
                    corrected_cmd = f"{cmd} --namespace=staging"
                    logging.info(f"Auto-correcting command: {cmd} -> {corrected_cmd}")
                    allowed_corrected, corr_reason = opa_check_command(corrected_cmd)
                    if allowed_corrected:
                        allowed_commands.append(corrected_cmd)
                    else:
                        rejected_commands.append((cmd, reason))
                else:
                    rejected_commands.append((cmd, reason))
        
        if not allowed_commands:
            msg = "❌ Generated commands violate policy constraints:\n"
            for cmd, reason in rejected_commands:
                msg += f"- {cmd}: {reason}\n"
            yield {"stage": "final", "message": msg}
            return

        yield {"stage": "commands", "message": f"🔧 *Generated Kubernetes Commands:*\n```{chr(10).join(allowed_commands)}```"}

        # Stage 4: Execute the allowed commands
        execution_output = execute_kubectl_commands(allowed_commands, delay=5)
        logging.info(f"Initial execution output: {execution_output}")

        if "error:" not in execution_output.lower():
            yield {"stage": "final", "message": f"✅ *Execution Results:*\n```{execution_output}```"}
            return

        # Stage 5: Handle errors and refine commands
        error_message = extract_error_from_output(execution_output)
        logging.info(f"Detected error: {error_message}")
        yield {"stage": "initial_error", "message": f"❌ *Initial Execution Results (with error):*\n```{execution_output}```"}
        
        refined_commands = refine_commands(text, commands, error_message, model, tokenizer)
        logging.info(f"Refined Commands: {refined_commands}")
        if not refined_commands:
            yield {"stage": "final", "message": "⚠️ Unable to refine commands after error."}
            return
        
        yield {"stage": "refined_commands", "message": f"🔧 *Refined Kubernetes Commands:*\n```{chr(10).join(refined_commands)}```"}
        
        refined_execution_output = execute_kubectl_commands(refined_commands, delay=10)
        logging.info(f"Refined execution output: {refined_execution_output}")
        yield {"stage": "final", "message": f"✅ *Refined Execution Results:*\n```{refined_execution_output}```"}
    
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        yield {"stage": "final", "message": f"❌ Error processing request: {e}"}
