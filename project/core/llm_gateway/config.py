"""
LLM Gateway Configuration (Python Version)

This file replaces the static `config.yaml` and serves as the central "Administrative Panel"
for managing LLM providers, models, and routing strategies.

It defines:
1.  THE GARAGE (`MODELS_REGISTRY`): A comprehensive catalog of all available models and their capabilities.
2.  ROUTER SETTINGS (`MODEL_GROUPS`): flexible groups defining which models to use for specific tasks (Coding, Reasoning) and their fallback chains.
"""

# --- Providers ---
PROVIDER_GOOGLE = "google"
PROVIDER_MISTRAL = "mistral"
PROVIDER_GROQ = "groq"
PROVIDER_COHERE = "cohere"
PROVIDER_CEREBRAS = "cerebras"

# --- THE GARAGE: Complete Model Registry ---
# Each entry contains metadata and the provider mapping.
MODELS_REGISTRY = {
    # --- GOOGLE GEMINI MODELS (Updated 22.11.2025) ---
    # 2.5 Pro / 3.0 Pro
    "gemini-3-pro-preview": {"provider": PROVIDER_GOOGLE, "mode": "reasoning", "description": "Gemini 3 Pro Preview."},
    "gemini-2.5-pro": {"provider": PROVIDER_GOOGLE, "mode": "reasoning", "description": "Gemini 2.5 Pro."},
    "gemini-2.5-pro-preview-06-05": {"provider": PROVIDER_GOOGLE, "mode": "reasoning", "description": "Gemini 2.5 Pro Preview (June)."},
    "gemini-2.5-pro-preview-05-06": {"provider": PROVIDER_GOOGLE, "mode": "reasoning", "description": "Gemini 2.5 Pro Preview (May)."},
    "gemini-2.5-pro-preview-03-25": {"provider": PROVIDER_GOOGLE, "mode": "reasoning", "description": "Gemini 2.5 Pro Preview (March)."},
    "gemini-pro-latest": {"provider": PROVIDER_GOOGLE, "mode": "reasoning", "description": "Alias for latest Pro."},

    # 2.0 Pro / Exp
    "gemini-2.0-pro-exp": {"provider": PROVIDER_GOOGLE, "mode": "reasoning", "description": "Gemini 2.0 Pro Experimental."},
    "gemini-2.0-pro-exp-02-05": {"provider": PROVIDER_GOOGLE, "mode": "reasoning", "description": "Gemini 2.0 Pro Exp (Feb)."},
    "gemini-exp-1206": {"provider": PROVIDER_GOOGLE, "mode": "reasoning", "description": "Gemini Experimental 1206."},

    # Flash Models
    "gemini-2.5-flash": {"provider": PROVIDER_GOOGLE, "mode": "reasoning", "description": "Gemini 2.5 Flash."},
    "gemini-flash-latest": {"provider": PROVIDER_GOOGLE, "mode": "reasoning", "description": "Alias for latest Flash."},
    "gemini-2.0-flash": {"provider": PROVIDER_GOOGLE, "mode": "reasoning", "description": "Gemini 2.0 Flash."},
    "gemini-2.0-flash-thinking-exp": {"provider": PROVIDER_GOOGLE, "mode": "reasoning", "description": "Gemini 2.0 Flash Thinking."},
    "gemini-2.0-flash-thinking-exp-01-21": {"provider": PROVIDER_GOOGLE, "mode": "reasoning", "description": "Gemini 2.0 Flash Thinking (Jan)."},

    # Lite Models
    "gemini-2.0-flash-lite": {"provider": PROVIDER_GOOGLE, "mode": "reasoning", "description": "Gemini 2.0 Flash Lite."},
    "gemini-flash-lite-latest": {"provider": PROVIDER_GOOGLE, "mode": "reasoning", "description": "Alias for latest Flash Lite."},

    # Gemma
    "gemma-3-27b-it": {"provider": PROVIDER_GOOGLE, "description": "Gemma 3 27B Instruct."},
    "gemma-3-12b-it": {"provider": PROVIDER_GOOGLE, "description": "Gemma 3 12B Instruct."},

    # --- MISTRAL MODELS ---
    "codestral-2501": {"provider": PROVIDER_MISTRAL, "description": "Mistral Codestral 2501."},
    "mistral-large-2411": {"provider": PROVIDER_MISTRAL, "description": "Mistral Large 2."},
    "mistral-small-2501": {"provider": PROVIDER_MISTRAL, "description": "Mistral Small 3."},
    "open-mistral-7b": {"provider": PROVIDER_MISTRAL, "description": "Mistral 7B."},

    # --- CEREBRAS MODELS ---
    "gpt-oss-120b": {"provider": PROVIDER_CEREBRAS, "description": "GPT-OSS 120B."},
    "llama-3.3-70b": {"provider": PROVIDER_CEREBRAS, "description": "Llama 3.3 70B via Cerebras."},
    "llama-3.1-8b": {"provider": PROVIDER_CEREBRAS, "description": "Llama 3.1 8B via Cerebras."},

    # --- GROQ MODELS ---
    "llama-3.1-8b-instant": {"provider": PROVIDER_GROQ, "description": "Llama 3.1 8B Instant via Groq."},
    "llama-3.3-70b-versatile": {"provider": PROVIDER_GROQ, "description": "Llama 3.3 70B Versatile via Groq."},

    # --- COHERE MODELS ---
    "command-r-plus-08-2024": {"provider": PROVIDER_COHERE, "description": "Command R+."},
    "command-r7b-12-2024": {"provider": PROVIDER_COHERE, "description": "Command R7B."}
}


# --- ROUTER SETTINGS: Model Groups & Fallback Chains ---
# Updated Logic:
# 1. Expert/Enhanced modes prioritize Gemini 2.5/Pro variants.
# 2. Flash/Codestral are used as fallback only.
# 3. Different "preview" versions are chained to maximize Rate Limits.

MODEL_GROUPS = {
    # =========================================================================
    # ENHANCED MODE (Strong Models / Experts)
    # =========================================================================

    # Coding: Top-tier coding models
    "enhanced_coding": [
        "gemini-2.5-pro",                 # Primary
        "gemini-3-pro-preview",           # Bleeding Edge
        "gemini-2.5-pro-preview-06-05",   # Fallback 1
        "gemini-2.5-pro-preview-05-06",   # Fallback 2
        "mistral-large-2411",             # Non-Google Top Tier
        "codestral-2501",                 # Mid-Tier Expert (Last Resort)
        "gemini-2.5-flash"                # Flash fallback
    ],

    # Reasoning: Top-tier analysis models
    "enhanced_reasoning": [
        "gemini-2.5-pro",
        "mistral-large-2411",
        "gpt-oss-120b"
    ],

    # Librarian: RAG/Memory tasks
    # Prioritize Flash for speed/context balance, Pro for depth.
    "librarian_group": [
        "gemini-2.5-flash",
        "gemini-pro-latest",
        "command-r-plus-08-2024" # Cohere as deep fallback
    ],

    # =========================================================================
    # CLASSIC MODE (Weak/Medium Models)
    # =========================================================================

    # Coding: Fast, smaller models
    "classic_coding": [
        "gpt-oss-120b",
        "gemini-flash-latest",
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant"
    ],

    # Reasoning: Planner
    "classic_reasoning": [
        "llama-3.3-70b",
        "gpt-oss-120b",
        "gemini-2.5-flash-lite",
        "mistral-small-2501"
    ],

    "classic_secondary_reasoning": [
        "gpt-oss-120b",
        "llama-3.3-70b"
    ],

    # =========================================================================
    # WEAK MODE (Stress Testing)
    # =========================================================================
    "weak_coding": [
        "llama-3.1-8b-instant",
        "open-mistral-7b"
    ],

    "weak_reasoning": [
        "llama-3.1-8b-instant",
        "open-mistral-7b"
    ],

    # =========================================================================
    # LEGACY ALIASES
    # =========================================================================
    "coding_model_group": ["gemini-2.5-pro", "codestral-2501"],
    "reasoning_model_group": ["gemini-2.5-pro", "mistral-large-2411"],
}

def get_model_config(model_name: str) -> dict:
    """Retrieves the configuration for a specific model from the Registry."""
    return MODELS_REGISTRY.get(model_name)

def get_model_group(group_name: str) -> list[str]:
    """Retrieves the list of models for a specific group."""
    return MODEL_GROUPS.get(group_name, [])
