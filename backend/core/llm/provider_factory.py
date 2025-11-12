"""
LLM Provider Factory and Manager (2025)
Centralized management for all LLM providers
Supports: OpenAI, Anthropic, Google Gemini, Grok
"""
from typing import Dict, Optional, Type, List
from enum import Enum
import logging

from .base import BaseLLMProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .grok_provider import GrokProvider
from .gemini_provider import GeminiProvider

logger = logging.getLogger(__name__)


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


def initialize_providers_from_yaml(config_path: Optional[str] = None):
    """
    Initialize providers from YAML configuration file

    This supports multiple providers with custom names.
    Configuration file format:

    ```yaml
    default_provider_id: openai_personal
    providers:
      - provider_id: openai_personal
        provider_type: openai
        display_name: "Personal OpenAI Account"
        api_key_env: OPENAI_PERSONAL_KEY
        default_model: gpt-4
        enabled: true

      - provider_id: openai_work
        provider_type: openai
        display_name: "Work OpenAI Account"
        api_key_env: OPENAI_WORK_KEY
        default_model: gpt-3.5-turbo
        enabled: true

      - provider_id: claude_main
        provider_type: anthropic
        display_name: "Main Claude Account"
        api_key_env: ANTHROPIC_API_KEY
        default_model: claude-3-5-sonnet-20241022
        enabled: true
    ```

    Args:
        config_path: Path to YAML configuration file.
                    If None, will search default locations.

    Returns:
        Number of providers initialized
    """
    from .config_loader import LLMConfigLoader

    manager = get_global_manager()

    # Load configuration
    if config_path:
        llm_config = LLMConfigLoader.load_from_file(config_path)
    else:
        llm_config = LLMConfigLoader.load_from_default_paths()
        if not llm_config:
            logger.warning("No configuration file found, using default configuration")
            llm_config = LLMConfigLoader.create_default_config()

    # Initialize providers
    initialized_count = 0
    for provider_config in llm_config.providers:
        if not provider_config.enabled:
            logger.info(f"Skipping disabled provider: {provider_config.display_name}")
            continue

        api_key = provider_config.get_api_key()
        if not api_key:
            logger.warning(
                f"API key not found for {provider_config.display_name} "
                f"(environment variable: {provider_config.api_key_env})"
            )
            continue

        try:
            # Convert provider type string to enum
            provider_type = ProviderType(provider_config.provider_type)

            # Add provider with custom name
            manager.add_provider(
                name=provider_config.provider_id,
                provider_type=provider_type,
                api_key=api_key,
                base_url=provider_config.base_url,
                set_as_default=(
                    provider_config.provider_id == llm_config.default_provider_id
                    or initialized_count == 0
                )
            )

            # Set default model if specified
            provider = manager.get_provider(provider_config.provider_id)
            if provider_config.default_model:
                provider.default_model = provider_config.default_model

            logger.info(
                f"Initialized provider: {provider_config.display_name} "
                f"(ID: {provider_config.provider_id})"
            )
            initialized_count += 1

        except Exception as e:
            logger.error(
                f"Failed to initialize provider {provider_config.display_name}: {e}"
            )

    if initialized_count == 0:
        logger.warning("No providers were initialized")
    else:
        logger.info(f"Successfully initialized {initialized_count} provider(s)")

    return initialized_count


def get_provider_display_names() -> Dict[str, str]:
    """
    Get mapping of provider IDs to display names

    Returns:
        Dictionary mapping provider_id to display_name
    """
    from .config_loader import load_llm_config

    config = load_llm_config()
    return {
        p.provider_id: p.display_name
        for p in config.providers
    }
