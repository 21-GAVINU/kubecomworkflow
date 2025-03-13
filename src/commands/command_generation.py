import logging
import torch
from src.config.config import MAX_NEW_TOKENS  # Adjust as needed

def generate_cot(instruction: str, model, tokenizer) -> str:
    """
    Generates a Chain-of-Thought (CoT) reasoning from the given instruction.
    """
    logging.info(f"Generating Chain-of-Thought for instruction: {instruction}")
    messages = [
        {
            "role": "system", 
            "content": "Provide a detailed chain-of-thought reasoning for the following task."
        },
        {
            "role": "user", 
            "content": instruction
        }
    ]
    inputs = tokenizer.apply_chat_template(
        messages,
        return_tensors="pt",
        add_generation_prompt=True
    ).to(model.device)

    outputs = model.generate(
        inputs,
        max_new_tokens=150,
        num_beams=3,
        early_stopping=True,
        repetition_penalty=1.2,
        do_sample=False,
        temperature=0.0,
        num_return_sequences=1,
        pad_token_id=tokenizer.eos_token_id,
        eos_token_id=tokenizer.eos_token_id,
        bad_words_ids=[[tokenizer.encode("\n")[0]]]
    )
    cot = tokenizer.decode(outputs[0], skip_special_tokens=True)
    logging.info(f"Generated CoT: {cot}")
    return cot

def generate_commands_from_cot(cot: str, model, tokenizer) -> list:
    """
    Generates kubectl commands based on the provided Chain-of-Thought (CoT).
    """
    logging.info("Generating kubectl commands from CoT.")
    messages = [
        {
            "role": "system", 
            "content": "Generate kubectl commands to implement the following reasoning. Output only commands."
        },
        {
            "role": "assistant", 
            "content": f"Chain-of-Thought: {cot}"
        }
    ]
    inputs = tokenizer.apply_chat_template(
        messages,
        return_tensors="pt",
        add_generation_prompt=True
    ).to(model.device)

    outputs = model.generate(
        inputs,
        max_new_tokens=150,
        num_beams=3,
        early_stopping=True,
        repetition_penalty=1.2,
        do_sample=False,
        temperature=0.0,
        num_return_sequences=1,
        pad_token_id=tokenizer.eos_token_id,
        eos_token_id=tokenizer.eos_token_id,
        bad_words_ids=[[tokenizer.encode("\n")[0]]]
    )
    full_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Extract commands from the full output (for example, split by newlines)
    commands = [
        line.strip() 
        for line in full_output.split("\n") 
        if line.strip().startswith("kubectl")
    ]
    logging.info(f"Extracted Commands: {commands}")
    return commands

def refine_commands_with_error(
    intent: str,
    previous_commands: list,
    error_message: str,
    model,
    tokenizer
) -> list:
    """
    Re-prompts the model to refine kubectl commands given the original intent,
    previously attempted commands, and an error message from execution.
    """
    logging.info("Refining commands with error feedback...")
    # System prompt: instruct the model to fix the commands
    messages = [
        {
            "role": "system",
            "content": (
                "You are a Kubernetes command generator. You produce refined kubectl commands "
                "based on errors encountered. Think step by step."
            )
        },
        {
            "role": "assistant",
            "content": (
                f"Original Intent: {intent}\n\n"
                f"Previously tried commands: {previous_commands}\n\n"
                f"Error encountered: {error_message}\n\n"
                "Now refine your chain-of-thought and generate corrected kubectl commands. "
                "Output only the commands."
            )
        }
    ]
    inputs = tokenizer.apply_chat_template(
        messages,
        return_tensors="pt",
        add_generation_prompt=True
    ).to(model.device)

    outputs = model.generate(
        inputs,
        max_new_tokens=150,
        num_beams=3,
        early_stopping=True,
        repetition_penalty=1.2,
        do_sample=False,
        temperature=0.0,
        num_return_sequences=1,
        pad_token_id=tokenizer.eos_token_id,
        eos_token_id=tokenizer.eos_token_id,
        bad_words_ids=[[tokenizer.encode("\n")[0]]]
    )
    raw_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
    logging.info(f"Refined commands output: {raw_output}")

    # Extract lines that start with "kubectl"
    refined_commands = [
        line.strip()
        for line in raw_output.split("\n")
        if line.strip().startswith("kubectl")
    ]
    logging.info(f"Refined Commands: {refined_commands}")
    return refined_commands
