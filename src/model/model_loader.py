from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from peft import PeftModel
from src.config.config import BASE_MODEL_NAME, ADAPTER_PATH

def load_model():
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_NAME, use_fast=False)
    base_model = AutoModelForCausalLM.from_pretrained(BASE_MODEL_NAME, torch_dtype=torch.float16).to("cuda")

    # Load adapter
    model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)
    model.to("cuda")

    return model, tokenizer

