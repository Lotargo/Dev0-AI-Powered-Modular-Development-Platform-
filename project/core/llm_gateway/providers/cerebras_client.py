
"""
Client for interacting with Cerebras's API services using httpx.
"""
import httpx
import json

class CerebrasClient:
    """
    Handles the API requests to Cerebras's models.
    """
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Cerebras API key is required.")
        self.api_key = api_key
        self.base_url = "https://api.cerebras.ai/v1"

    async def make_request(self, model_name: str, prompt: str, **kwargs) -> str:
        """
        Makes an asynchronous request to the specified Cerebras model.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
        }

        if "reasoning_effort" in kwargs:
            payload["reasoning_effort"] = kwargs["reasoning_effort"]

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=300.0
                )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            raise IOError(f"Cerebras API call failed: {e}")

    async def list_models(self):
        """
        Fetches the list of available models from Cerebras.
        """
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=headers,
                    timeout=30.0
                )
            response.raise_for_status()
            return [model["id"] for model in response.json()["data"]]
        except Exception as e:
            raise IOError(f"Cerebras API call to list models failed: {e}")
