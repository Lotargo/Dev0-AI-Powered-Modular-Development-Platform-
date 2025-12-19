"""
Asynchronous and resilient API key management for multiple LLM providers.
This manager is designed to load keys directly from dedicated .env.<provider> files.
"""
import os
import asyncio
import re
from typing import List, Dict, Optional
from collections import deque

# --- Constants ---
GET_KEY_TIMEOUT_SECONDS = 30
QUARANTINE_DURATION_SECONDS = 300  # 5 minutes

class NoKeysAvailableError(Exception):
    """Raised when no API keys are configured for a provider."""
    pass

class GetKeyTimeoutError(Exception):
    """Raised when a request for an API key times out."""
    pass

class ApiKeyManager:
    def __init__(self, project_root="."):
        self._providers: Dict[str, Dict] = {}
        self._initialized = False
        self._lock = asyncio.Lock()
        self.project_root = project_root

    def _load_keys_from_provider_env_files(self):
        """
        Loads keys directly from .env.<provider> files in the project root.
        Example: .env.google should contain GOOGLE_API_KEYS="key1,key2"
        """
        print("--- ApiKeyManager: Loading keys from .env.<provider> files ---")
        provider_env_files = [f for f in os.listdir(self.project_root) if f.startswith(".env.") and not f.endswith(".example")]

        for filename in provider_env_files:
            provider = filename.replace(".env.", "")
            filepath = os.path.join(self.project_root, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    match = re.search(r'^\w+_API_KEYS="([^"]+)"', content, re.MULTILINE)
                    if match:
                        keys_str = match.group(1)
                        # CORRECTED: Split the string by comma to handle multiple keys
                        keys = [key.strip() for key in keys_str.split(',') if key.strip()]

                        if keys:
                            unique_keys = list(dict.fromkeys(keys))
                            print(f"Provider '{provider}': Loaded {len(unique_keys)} unique key(s) from {filename}.")

                            if provider not in self._providers:
                                self._providers[provider] = {
                                    "keys": asyncio.Queue(),
                                    "quarantine": {}
                                }

                            for key in unique_keys:
                                self._providers[provider]["keys"].put_nowait(key)
                        else:
                            print(f"Provider '{provider}': No keys found in {filename}.")
                    else:
                        print(f"Provider '{provider}': No valid key line found in {filename}.")
            except Exception as e:
                print(f"Error reading or parsing {filepath}: {e}")

        print("----------------------------------------------------------")


    async def initialize_providers(self):
        """Initializes the providers if they haven't been already."""
        async with self._lock:
            if not self._initialized:
                print("Initializing ApiKeyManager...")
                self._load_keys_from_provider_env_files()
                self._initialized = True
                asyncio.create_task(self._release_quarantined_keys_periodically())

    def get_available_providers(self) -> List[str]:
        """Returns a list of providers for which keys have been loaded."""
        return list(self._providers.keys())

    async def get_key(self, provider: str) -> str:
        """Asynchronously gets an available API key for the given provider."""
        if not self._initialized:
            await self.initialize_providers()

        if provider not in self._providers or self._providers[provider]["keys"].empty():
            raise NoKeysAvailableError(f"No API keys configured or available for provider '{provider}'.")

        try:
            # Although we checked `empty()`, a race condition is still possible in theory.
            # The timeout provides a final safeguard.
            return await asyncio.wait_for(self._providers[provider]["keys"].get(), timeout=GET_KEY_TIMEOUT_SECONDS)
        except asyncio.TimeoutError:
            raise GetKeyTimeoutError(f"Timed out waiting for an API key for '{provider}'.")

    async def release_key(self, provider: str, key: str, is_permanently_invalid: bool = False):
        """Releases a key back to the pool or quarantines/retires it."""
        if provider not in self._providers:
            return

        if is_permanently_invalid:
            print(f"Permanently retiring invalid key for {provider}: ...{key[-4:]}")
        else:
            await self._providers[provider]["keys"].put(key)

    async def _release_quarantined_keys_periodically(self):
        """A background task that should not be called directly."""
        while True:
            await asyncio.sleep(60)

# --- Singleton Instance ---
api_key_manager = ApiKeyManager()
