"""
Client for interacting with Mistral's API services via direct HTTP requests.
Replaces the deprecated SDK implementation.
"""
import httpx
import json

class MistralClient:
    """
    Handles the API requests to Mistral's models using httpx.
    """
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Mistral API key is required.")
        self.api_key = api_key
        self.base_url = "https://api.mistral.ai/v1"

    async def make_request(self, model_name: str, prompt: str, **kwargs) -> str:
        """
        Makes an asynchronous request to the specified Mistral model.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Construct messages.
        # If the gateway passes 'messages' in kwargs (e.g. from a chat history), use it.
        # Otherwise, wrap the prompt in a standard user message.
        messages = kwargs.get("messages", [{"role": "user", "content": prompt}])

        payload = {
            "model": model_name,
            "messages": messages
        }

        # Pass optional parameters
        if "temperature" in kwargs:
            payload["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            payload["max_tokens"] = kwargs["max_tokens"]

        # Handle 'mode' parameter from config (e.g. 'reasoning' -> json_mode?)
        # Mistral supports response_format={"type": "json_object"}
        if kwargs.get("mode") == "json" or kwargs.get("response_format") == "json_object":
             payload["response_format"] = {"type": "json_object"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60.0
                )

                if response.status_code != 200:
                    raise IOError(f"Mistral API Error {response.status_code}: {response.text}")

                data = response.json()
                return data["choices"][0]["message"]["content"]

        except httpx.RequestError as e:
            raise IOError(f"Mistral connection error: {e}")
        except Exception as e:
            raise IOError(f"Mistral API call failed: {e}")
