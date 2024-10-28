import requests
from config import API_KEY, API_URL

class KubernetesCommandGenerator:
    """Class to generate Kubernetes commands based on parsed intents."""

    @staticmethod
    def generate_multi_command(intent: str) -> str:
        """Generate a sequence of Kubernetes commands for multi-step tasks."""
        if not API_KEY or not API_URL:
            raise ValueError("API key or URL not configured")

        # Set headers and payload for API request
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"Generate a sequence of Kubernetes commands for: {intent}. "
                                    "The commands should follow the proper order. For example, create a namespace if needed, "
                                    "then create a deployment, and so on. Only provide the commands without any explanations."
                        }
                    ]
                }
            ]
        }

        # Make the POST request
        response = requests.post(f"{API_URL}?key={API_KEY}", headers=headers, json=data)

        # Check if the request was successful
        if response.status_code == 200:
            # Extract the commands
            commands_content = response.json()['candidates'][0]['content']['parts'][0]['text']
            return commands_content.strip()  # Return only the commands
        else:
            raise Exception(f"Request failed with status code {response.status_code}: {response.text}")
