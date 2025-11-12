"""
LLM Provider Factory and Manager (2025)
Centralized management for all LLM providers
Supports: OpenAI, Anthropic, Google Gemini, Grok
"""
from typing import Dict, Optional, Type, List
from enum import Enum

from .base import BaseLLMProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .grok_provider import GrokProvider
from .gemini_provider import GeminiProvider


class ProviderType(str, Enum):
    """Supported LLM provider types (2025)"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROK = "grok"
    GEMINI = "gemini"


class LLMProviderFactory:
    """Factory for creating LLM provider instances (2025)"""

    _providers: Dict[ProviderType, Type[BaseLLMProvider]] = {
        ProviderType.OPENAI: OpenAIProvider,
        ProviderType.ANTHROPIC: AnthropicProvider,
        ProviderType.GROK: GrokProvider,
        ProviderType.GEMINI: GeminiProvider,
    }

    @classmethod
    def create(
        cls,
        provider_type: ProviderType,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: int = 120
    ) -> BaseLLMProvider:
        """
        Create a new LLM provider instance

        Args:
            provider_type: Type of provider to create
            api_key: API key for the provider
            base_url: Optional custom base URL
            timeout: Request timeout in seconds

        Returns:
            Provider instance

        Raises:
            ValueError: If provider type is not supported
        """
        if provider_type not in cls._providers:
            raise ValueError(f"Unsupported provider type: {provider_type}")

        provider_class = cls._providers[provider_type]
        return provider_class(api_key=api_key, base_url=base_url, timeout=timeout)

    @classmethod
    def get_supported_providers(cls) -> List[str]:
        """Get list of supported provider types"""
        return [p.value for p in ProviderType]

    @classmethod
    def get_provider_info(cls, provider_type: ProviderType) -> Dict[str, any]:
        """Get information about a provider"""
        if provider_type not in cls._providers:
            raise ValueError(f"Unsupported provider type: {provider_type}")

        provider_class = cls._providers[provider_type]
        # Create a temporary instance to get capabilities (without API key)
        try:
            temp_instance = provider_class(api_key="dummy")
            return {
                "name": temp_instance.provider_name,
                "supports_tools": temp_instance.supports_tool_calling(),
                "supports_structured_output": temp_instance.supports_structured_output(),
                "supported_models": temp_instance.get_supported_models()
            }
        except:
            return {
                "name": provider_type.value,
                "supports_tools": False,
                "supports_structured_output": False,
                "supported_models": []
            }


class LLMProviderManager:
    """
    Manager for multiple LLM provider instances
    Handles provider lifecycle and routing
    """

    def __init__(self):
        self._providers: Dict[str, BaseLLMProvider] = {}
        self._default_provider: Optional[str] = None

    def add_provider(
        self,
        name: str,
        provider_type: ProviderType,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: int = 120,
        set_as_default: bool = False
    ) -> BaseLLMProvider:
        """
        Add a new provider instance

        Args:
            name: Unique name for this provider instance
            provider_type: Type of provider
            api_key: API key
            base_url: Optional custom base URL
            timeout: Request timeout
            set_as_default: Set as default provider

        Returns:
            Created provider instance
        """
        if name in self._providers:
            raise ValueError(f"Provider with name '{name}' already exists")

        provider = LLMProviderFactory.create(
            provider_type=provider_type,
            api_key=api_key,
            base_url=base_url,
            timeout=timeout
        )

        self._providers[name] = provider

        if set_as_default or not self._default_provider:
            self._default_provider = name

        return provider

    def get_provider(self, name: Optional[str] = None) -> BaseLLMProvider:
        """
        Get a provider by name, or default provider if name is None

        Args:
            name: Provider name, or None for default

        Returns:
            Provider instance

        Raises:
            ValueError: If provider not found or no default set
        """
        if name is None:
            if not self._default_provider:
                raise ValueError("No default provider set")
            name = self._default_provider

        if name not in self._providers:
            raise ValueError(f"Provider '{name}' not found")

        return self._providers[name]

    def remove_provider(self, name: str):
        """Remove a provider"""
        if name in self._providers:
            del self._providers[name]
            if self._default_provider == name:
                self._default_provider = None

    def set_default_provider(self, name: str):
        """Set default provider"""
        if name not in self._providers:
            raise ValueError(f"Provider '{name}' not found")
        self._default_provider = name

    def list_providers(self) -> List[Dict[str, any]]:
        """List all registered providers"""
        return [
            {
                "name": name,
                "provider_type": provider.provider_name,
                "is_default": name == self._default_provider,
                "supports_tools": provider.supports_tool_calling(),
                "supports_structured_output": provider.supports_structured_output(),
            }
            for name, provider in self._providers.items()
        ]

    def get_default_provider_name(self) -> Optional[str]:
        """Get default provider name"""
        return self._default_provider


# Global provider manager instance
_global_manager: Optional[LLMProviderManager] = None


def get_global_manager() -> LLMProviderManager:
    """Get or create global provider manager"""
    global _global_manager
    if _global_manager is None:
        _global_manager = LLMProviderManager()
    return _global_manager


def initialize_providers_from_config(config: Dict[str, any]):
    """
    Initialize providers from configuration

    Args:
        config: Configuration dictionary with provider settings
    """
    manager = get_global_manager()

    # Add OpenAI if configured
    if config.get("OPENAI_API_KEY"):
        try:
            manager.add_provider(
                name="openai",
                provider_type=ProviderType.OPENAI,
                api_key=config["OPENAI_API_KEY"],
                set_as_default=True
            )
        except Exception as e:
            print(f"Failed to initialize OpenAI provider: {e}")

    # Add Anthropic if configured
    if config.get("ANTHROPIC_API_KEY"):
        try:
            manager.add_provider(
                name="anthropic",
                provider_type=ProviderType.ANTHROPIC,
                api_key=config["ANTHROPIC_API_KEY"],
                set_as_default=not manager.get_default_provider_name()
            )
        except Exception as e:
            print(f"Failed to initialize Anthropic provider: {e}")

    # Add Grok if configured
    if config.get("GROK_API_KEY"):
        try:
            manager.add_provider(
                name="grok",
                provider_type=ProviderType.GROK,
                api_key=config["GROK_API_KEY"],
                set_as_default=not manager.get_default_provider_name()
            )
        except Exception as e:
            print(f"Failed to initialize Grok provider: {e}")

    # Add Gemini if configured
    if config.get("GEMINI_API_KEY"):
        try:
            manager.add_provider(
                name="gemini",
                provider_type=ProviderType.GEMINI,
                api_key=config["GEMINI_API_KEY"],
                set_as_default=not manager.get_default_provider_name()
            )
        except Exception as e:
            print(f"Failed to initialize Gemini provider: {e}")
