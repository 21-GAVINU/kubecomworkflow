import requests
from config import API_KEY, API_URL

class KubernetesCommandGenerator:
    """Class to generate Kubernetes commands based on parsed intents."""

    @staticmethod
    def generate_command(intent: str) -> str:
        """Generate a Kubernetes command using an external API."""
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
                        {"text": f"Generate a Kubernetes command for: {intent}. Only provide the command without any explanations."}
                    ]
                }
            ]
        }

        # Make the POST request
        response = requests.post(f"{API_URL}?key={API_KEY}", headers=headers, json=data)

        # Check if the request was successful
        if response.status_code == 200:
            # Extract the command
            command_content = response.json()['candidates'][0]['content']['parts'][0]['text']
            return command_content.strip()  # Return only the command
        else:
            raise Exception(f"Request failed with status code {response.status_code}: {response.text}")
