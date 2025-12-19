"""
Client for interacting with Google's Generative AI services.
"""
import google.generativeai as genai
from typing import Dict, Any

# Define a dummy tool to force the model into a reasoning mode
DUMMY_TOOL = {"function_declarations": [{"name": "execute_code", "description": "Executes python code"}]}

class GoogleClient:
    """
    Handles the API requests to Google's Gemini models.
    """
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Google API key is required.")
        genai.configure(api_key=api_key)

    async def make_request(self, model_name: str, prompt: str, **kwargs) -> str:
        """
        Makes an asynchronous request to the specified Google model.
        If 'mode' is 'reasoning', it passes a dummy tool to activate that behavior.
        """
        try:
            model_kwargs = {}
            if kwargs.get("mode") == "reasoning":
                model_kwargs["tools"] = DUMMY_TOOL

            model = genai.GenerativeModel(model_name, **model_kwargs)

            response = await model.generate_content_async(prompt)
            try:
                return response.text
            except Exception:
                # Handle cases where response contains function calls but no direct text
                parts_text = []
                if hasattr(response, "parts"):
                    for part in response.parts:
                        if hasattr(part, "text") and part.text:
                            parts_text.append(part.text)
                        if hasattr(part, "function_call") and part.function_call:
                            fc = part.function_call
                            # Serialize args if possible, or just stringify
                            parts_text.append(f"```python\n# Tool Call: {fc.name}({fc.args})\n```")
                if parts_text:
                    return "\n".join(parts_text)
                raise ValueError("Response contained no text or function calls.")

        except Exception as e:
            # Broadly catch exceptions from the API and raise a generic error
            # to be handled by the gateway's resilience logic.
            raise IOError(f"Google API call failed: {e}")
