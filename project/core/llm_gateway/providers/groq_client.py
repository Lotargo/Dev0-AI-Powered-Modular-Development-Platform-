
"""
Client for interacting with Groq's API services.
"""
from groq import AsyncGroq

class GroqClient:
    """
    Handles the API requests to Groq's models.
    """
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Groq API key is required.")
        self.client = AsyncGroq(api_key=api_key)

    async def make_request(self, model_name: str, prompt: str, **kwargs) -> str:
        """
        Makes an asynchronous request to the specified Groq model.
        """
        try:
            payload = {
                "messages": [{"role": "user", "content": prompt}],
                "model": model_name,
            }
            if "reasoning_effort" in kwargs:
                payload["reasoning_effort"] = kwargs["reasoning_effort"]

            chat_completion = await self.client.chat.completions.create(**payload)
            return chat_completion.choices[0].message.content
        except Exception as e:
            raise IOError(f"Groq API call failed: {e}")

    async def list_models(self):
        """
        Fetches the list of available models from Groq.
        """
        try:
            models = await self.client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            raise IOError(f"Groq API call to list models failed: {e}")
