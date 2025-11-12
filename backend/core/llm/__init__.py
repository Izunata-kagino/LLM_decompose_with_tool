"""
LLM Integration Module (2025)

This module provides unified interface for multiple LLM providers:
- OpenAI (GPT-5, GPT-4.1, O-series)
- Anthropic (Claude 4.5, 4.1, 4)
- Google Gemini (Gemini 2.5 Pro, Flash)
- Grok (Grok 4, Grok 3)

All providers support:
- Tool calling
- Structured output
- Streaming responses
"""

from .base import BaseLLMProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .grok_provider import GrokProvider
from .gemini_provider import GeminiProvider
from .provider_factory import (
    LLMProviderFactory,
    LLMProviderManager,
    ProviderType,
    get_global_manager,
    initialize_providers_from_config,
    initialize_providers_from_yaml,
    get_provider_display_names,
)
from .config_loader import (
    load_llm_config,
    LLMProvidersConfig,
    ProviderConfig,
    LLMConfigLoader,
)

__all__ = [
    # Base
    "BaseLLMProvider",

    # Providers
    "OpenAIProvider",
    "AnthropicProvider",
    "GrokProvider",
    "GeminiProvider",

    # Factory and Management
    "LLMProviderFactory",
    "LLMProviderManager",
    "ProviderType",
    "get_global_manager",
    "initialize_providers_from_config",
    "initialize_providers_from_yaml",
    "get_provider_display_names",

    # Configuration
    "load_llm_config",
    "LLMProvidersConfig",
    "ProviderConfig",
    "LLMConfigLoader",
]
