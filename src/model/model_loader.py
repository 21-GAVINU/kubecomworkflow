from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from peft import PeftModel
from src.config.config import BASE_MODEL_NAME, ADAPTER_PATH
from peft.config import PeftConfig

# Define a list of keys to remove from kwargs
UNEXPECTED_KEYS = ["eva_config", "exclude_modules", "lora_bias"]

# Save the original from_peft_type method
original_from_peft_type = PeftConfig.from_peft_type

def patched_from_peft_type(**kwargs):
    # Remove any unexpected keys from the kwargs
    for key in UNEXPECTED_KEYS:
        if key in kwargs:
            kwargs.pop(key)
    return original_from_peft_type(**kwargs)

# Apply the monkey patch
PeftConfig.from_peft_type = patched_from_peft_type

def load_model():
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_NAME, use_fast=False)
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_NAME,
        torch_dtype=torch.float16  # Change to torch.float32 if testing on CPU
    ).to("cuda")  # Change to "cpu" if testing on CPU

    # Load adapter (the patched config will ignore unexpected keys)
    model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)
    model.to("cuda")  # Change to "cpu" if testing on CPU

    return model, tokenizer
