from generator import KubernetesCommandGenerator
from intent_parser import IntentParser
from utils import get_user_intent

if __name__ == "__main__":
    # Get user intent for Kubernetes command
    user_intent = get_user_intent()

    try:
        # Parse the user intent
        parsed_intent = IntentParser.parse_intent(user_intent)
        
        # Generate the Kubernetes commands for multi-step execution
        generated_commands = KubernetesCommandGenerator.generate_multi_command(parsed_intent)
        
        # Output the generated commands
        print("Generated Kubernetes Commands:\n", generated_commands)
    except Exception as e:
        print("Error:", e)
