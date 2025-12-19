
"""
Client for interacting with Cohere's API services.
"""
import cohere

class CohereClient:
    """
    Handles the API requests to Cohere's models.
    """
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Cohere API key is required.")
        self.client = cohere.Client(api_key=api_key)
        self.async_client = cohere.AsyncClient(api_key=api_key)


    async def make_request(self, model_name: str, prompt: str, **kwargs) -> str:
        """
        Makes an asynchronous request to the specified Cohere model.
        """
        try:
            response = await self.async_client.chat(
                model=model_name,
                message=prompt
            )
            return response.text
        except Exception as e:
            raise IOError(f"Cohere API call failed: {e}")

    def list_models(self):
        """
        Fetches the list of available models from Cohere.
        """
        try:
            models = self.client.models.list()
            return [model.name for model in models]
        except Exception as e:
            raise IOError(f"Cohere API call to list models failed: {e}")
