import re

def extract_kubectl_commands(generated_text):
    """
    Extracts `kubectl` commands.
    """
    command_pattern = r"^\s*\d*[:.]?\s*(kubectl\s.+)$"
    matches = re.findall(command_pattern, generated_text, re.MULTILINE)
    
    return [match.strip() for match in matches]
