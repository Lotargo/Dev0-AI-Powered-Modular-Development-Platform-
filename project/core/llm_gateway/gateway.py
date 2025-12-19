"""
The primary LLM Gateway for handling API requests with resilience.
"""
import asyncio
from typing import Dict, Any, Optional
import os

from project.core.llm_gateway.key_manager import api_key_manager, GetKeyTimeoutError, NoKeysAvailableError
from project.core.llm_gateway.providers.google_client import GoogleClient
from project.core.llm_gateway.providers.mistral_client import MistralClient
from project.core.llm_gateway.providers.groq_client import GroqClient
from project.core.llm_gateway.providers.cohere_client import CohereClient
from project.core.llm_gateway.providers.cerebras_client import CerebrasClient

# Import the new Python configuration
from project.core.llm_gateway import config as gateway_config

# --- Provider Factory ---
PROVIDER_MAP = {
    "google": GoogleClient,
    "mistral": MistralClient,
    "groq": GroqClient,
    "cohere": CohereClient,
    "cerebras": CerebrasClient,
}

def get_provider_client(provider_name: str, api_key: str):
    client_class = PROVIDER_MAP.get(provider_name.lower())
    if not client_class:
        raise ValueError(f"Unsupported provider: {provider_name}")
    return client_class(api_key=api_key)


class LLMGateway:
    def __init__(self, key_manager=api_key_manager):
        # The key manager is passed in, but it's assumed it's also initialized lazily
        self._key_manager = key_manager
        print("LLMGateway initialized.")

    async def call(self, model_group: str, prompt: str, **kwargs) -> str:
        """
        Makes an API call to the appropriate LLM provider with fallback and resilience.
        """
        # Use the new config module to get the priority list
        model_priority_list = gateway_config.get_model_group(model_group)

        if not model_priority_list:
            raise ValueError(f"Model group '{model_group}' not found in router configuration.")

        last_error = None
        available_providers = self._key_manager.get_available_providers()

        for model_name in model_priority_list:
            # Use the new config module to get model details
            model_details = gateway_config.get_model_config(model_name)

            if not model_details:
                print(f"Warning: Model '{model_name}' not found in registry. Skipping.")
                continue

            provider = model_details['provider']

            # Proactively check if keys are available for the provider
            if provider not in available_providers:
                print(f"Warning: No API keys found for provider '{provider}'. Skipping model '{model_name}'.")
                continue

            api_key = None

            try:
                api_key = await self._key_manager.get_key(provider)

                client_class = PROVIDER_MAP.get(provider)
                if not client_class:
                    raise ValueError(f"Provider '{provider}' not supported.")

                client = client_class(api_key)
                print(f"--- Attempting call to {provider.upper()} model '{model_name}' ---")

                # Merge model details (like 'mode': 'reasoning') with runtime kwargs
                call_params = {**model_details, **kwargs, "prompt": prompt, "model_name": model_name}

                # Some clients expect 'model_name' in the call, others might use it from init or ignore it.
                # The Clients usually take specific args. Let's ensure we pass what's needed.
                # Our clients' make_request generally accepts **kwargs.

                response = await client.make_request(**call_params)

                await self._key_manager.release_key(provider, api_key)
                return response

            except (GetKeyTimeoutError, NoKeysAvailableError) as e:
                print(f"Key error for provider '{provider}': {e}. Trying next model in fallback chain.")
                last_error = e
                continue

            except Exception as e:
                print(f"Error with model '{model_name}': {e}")
                last_error = e
                is_auth_error = "401" in str(e) or "403" in str(e) or "API key" in str(e).lower()

                if api_key:
                    await self._key_manager.release_key(provider, api_key, is_permanently_invalid=is_auth_error)

                continue

        raise Exception(f"Failed to get a response from any model in the group '{model_group}'. Last error: {last_error}")

# --- Lazy Singleton Pattern ---
_llm_gateway_instance: Optional[LLMGateway] = None
_gateway_lock = asyncio.Lock()

async def _get_gateway_instance() -> LLMGateway:
    """Lazily initializes and returns the LLMGateway singleton instance."""
    global _llm_gateway_instance
    if _llm_gateway_instance is None:
        async with _gateway_lock:
            # Double-check locking for async
            if _llm_gateway_instance is None:
                # Crucially, we re-initialize the key manager here to ensure it picks up .env vars
                await api_key_manager.initialize_providers()
                _llm_gateway_instance = LLMGateway(key_manager=api_key_manager)
    return _llm_gateway_instance

from project.core.framework.observability import observable

@observable
async def execute(model_group: str, prompt: str, **kwargs) -> str:
    """Convenience function to lazily get and use the singleton gateway instance."""
    gateway = await _get_gateway_instance()
    return await gateway.call(model_group, prompt, **kwargs)
