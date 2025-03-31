import logging
import re
import torch
from src.config.config import MAX_NEW_TOKENS 

def generate_cot(instruction: str, model, tokenizer) -> str:
    """
    Generate the chain-of-thought (CoT) from the model in a series of steps.
    """
    logging.info(f"Generating Chain-of-Thought for instruction: {instruction}")
    
    messages = [
        {
            "role": "system", 
            "content": (
                "You are a Kubernetes expert assistant. Provide a step-based chain-of-thought reasoning for "
                "the following task. List each step in concise form. Output format:\n\n"
                "Step 1: <reasoning>\n"
                "Step 2: <reasoning>\n"
                "Step 3: <reasoning>\n\n"
            )
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
        max_new_tokens=200,
        do_sample=True,
        temperature=0.7,
        top_p=0.9,
        repetition_penalty=1.0,
        num_return_sequences=1,
        pad_token_id=tokenizer.eos_token_id,
        eos_token_id=tokenizer.eos_token_id
    )
    
    raw_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
    logging.info(f"Raw CoT output: {raw_output}")

    return raw_output.strip()

def generate_commands(cot: str, model, tokenizer) -> list:
    """
    Generates kubectl commands based on the provided Chain-of-Thought (CoT).
    """
    logging.info("Generating kubectl commands from CoT.")
    messages = [
        {
            "role": "system", 
            "content": (
                "You are a Kubernetes command generator. Given the chain-of-thought reasoning provided, "
                "generate valid kubectl commands that implement that reasoning. "
                "Output only the commands, each on a separate line, with no extra commentary. "
                "Each command must start with 'kubectl'."
            )
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
        do_sample=True,
        temperature=0.6,
        top_p=0.9,
        num_beams=1,
        early_stopping=True,
        repetition_penalty=1.0,
        num_return_sequences=1,
        pad_token_id=tokenizer.eos_token_id,
        eos_token_id=tokenizer.eos_token_id
    )
    full_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
    logging.info(f"Raw commands output: {full_output}")

    commands = [
        line.strip()
        for line in full_output.split("\n")
        if line.strip().startswith("kubectl")
    ]
    logging.info(f"Extracted Commands: {commands}")
    return commands

def refine_commands(intent: str, previous_commands: list, error_message: str, model, tokenizer) -> list:
    """
    Re-prompts the model to refine kubectl commands.
    """
    logging.info("Refining commands with error feedback...")
    messages = [
        {
            "role": "system",
            "content": (
                "You are a Kubernetes command generator. Your task is to produce corrected kubectl commands "
                "based on the following context. "
                "Think step by step and output only valid kubectl commands (one per line), each starting with 'kubectl'."
            )
        },
        {
            "role": "assistant",
            "content": (
                f"Original Intent: {intent}\n"
                f"Previously tried commands: {previous_commands}\n"
                f"Error encountered: {error_message}\n"
                "Refine your reasoning and generate corrected kubectl commands. "
                "Output only the commands, each on a new line, with no extra commentary."
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
        do_sample=True,
        temperature=0.6,
        top_p=0.9,
        num_beams=1,
        early_stopping=True,
        repetition_penalty=1.0,
        num_return_sequences=1,
        pad_token_id=tokenizer.eos_token_id,
        eos_token_id=tokenizer.eos_token_id
    )
    raw_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
    logging.info(f"Refined commands output: {raw_output}")
    
    refined_commands = [line.strip() for line in raw_output.split("\n") if line.strip().startswith("kubectl")]
    logging.info(f"Refined Commands: {refined_commands}")
    return refined_commands
