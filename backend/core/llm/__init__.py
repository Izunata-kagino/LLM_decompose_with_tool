"""
LLM Integration Module

This module provides unified interface for multiple LLM providers:
- OpenAI (GPT-4, GPT-3.5, etc.)
- Anthropic (Claude 3 family)
- Grok (X.AI)

All providers support:
- Tool calling
- Structured output
- Streaming responses
"""

from .base import BaseLLMProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .grok_provider import GrokProvider
from .provider_factory import (
    LLMProviderFactory,
    LLMProviderManager,
    ProviderType,
    get_global_manager,
    initialize_providers_from_config
)

__all__ = [
    # Base
    "BaseLLMProvider",

    # Providers
    "OpenAIProvider",
    "AnthropicProvider",
    "GrokProvider",

    # Factory and Management
    "LLMProviderFactory",
    "LLMProviderManager",
    "ProviderType",
    "get_global_manager",
    "initialize_providers_from_config",
]
