from generator import KubernetesCommandGenerator
from intent_parser import IntentParser
from utils import get_user_intent

if __name__ == "__main__":
    # Get user intent for Kubernetes command
    user_intent = get_user_intent()

    try:
        # Parse the user intent
        parsed_intent = IntentParser.parse_intent(user_intent)
        
        # Generate the Kubernetes command
        generated_command = KubernetesCommandGenerator.generate_command(parsed_intent)
        
        # Output the generated command
        print("Generated Kubernetes Command:\n", generated_command)
    except Exception as e:
        print("Error:", e)
