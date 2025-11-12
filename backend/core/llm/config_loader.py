"""
LLM Provider configuration system supporting multiple providers with custom names
"""
import yaml
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class ProviderConfig(BaseModel):
    """Configuration for a single LLM provider instance"""
    provider_id: str  # Unique identifier (e.g., "openai_personal")
    provider_type: str  # Type: openai, anthropic, gemini, grok
    display_name: str  # User-friendly name
    api_key_env: str  # Environment variable name for API key
    default_model: Optional[str] = None
    base_url: Optional[str] = None
    enabled: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def get_api_key(self) -> Optional[str]:
        """Get API key from environment variable"""
        return os.environ.get(self.api_key_env)

    def has_api_key(self) -> bool:
        """Check if API key is available"""
        return self.get_api_key() is not None


class LLMProvidersConfig(BaseModel):
    """Configuration for all LLM providers"""
    providers: List[ProviderConfig] = Field(default_factory=list)
    default_provider_id: Optional[str] = None

    def get_provider(self, provider_id: str) -> Optional[ProviderConfig]:
        """Get provider configuration by ID"""
        for provider in self.providers:
            if provider.provider_id == provider_id:
                return provider
        return None

    def get_providers_by_type(self, provider_type: str) -> List[ProviderConfig]:
        """Get all providers of a specific type"""
        return [p for p in self.providers if p.provider_type == provider_type]

    def get_enabled_providers(self) -> List[ProviderConfig]:
        """Get all enabled providers that have API keys"""
        return [
            p for p in self.providers
            if p.enabled and p.has_api_key()
        ]

    def get_default_provider(self) -> Optional[ProviderConfig]:
        """Get the default provider"""
        if self.default_provider_id:
            return self.get_provider(self.default_provider_id)

        # Return first enabled provider with API key
        enabled = self.get_enabled_providers()
        return enabled[0] if enabled else None


class LLMConfigLoader:
    """Loader for LLM provider configurations"""

    DEFAULT_CONFIG_PATHS = [
        "llm_providers.yaml",
        "config/llm_providers.yaml",
        ".config/llm_providers.yaml",
    ]

    @classmethod
    def load_from_file(cls, config_path: str) -> LLMProvidersConfig:
        """
        Load configuration from YAML file

        Args:
            config_path: Path to YAML configuration file

        Returns:
            LLMProvidersConfig object
        """
        path = Path(config_path)

        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not data:
            raise ValueError(f"Empty configuration file: {config_path}")

        # Parse configuration
        providers = []
        for provider_data in data.get('providers', []):
            provider = ProviderConfig(**provider_data)
            providers.append(provider)

        config = LLMProvidersConfig(
            providers=providers,
            default_provider_id=data.get('default_provider_id')
        )

        logger.info(f"Loaded {len(providers)} provider configurations from {config_path}")
        return config

    @classmethod
    def load_from_default_paths(cls) -> Optional[LLMProvidersConfig]:
        """
        Load configuration from default paths

        Returns:
            LLMProvidersConfig if found, None otherwise
        """
        for config_path in cls.DEFAULT_CONFIG_PATHS:
            path = Path(config_path)
            if path.exists():
                try:
                    return cls.load_from_file(str(path))
                except Exception as e:
                    logger.warning(f"Failed to load config from {config_path}: {e}")

        return None

    @classmethod
    def create_default_config(cls) -> LLMProvidersConfig:
        """
        Create a default configuration from environment variables

        This is a fallback when no config file exists
        """
        providers = []

        # OpenAI
        if os.environ.get("OPENAI_API_KEY"):
            providers.append(ProviderConfig(
                provider_id="openai_default",
                provider_type="openai",
                display_name="OpenAI (默认)",
                api_key_env="OPENAI_API_KEY",
                default_model="gpt-4"
            ))

        # Anthropic
        if os.environ.get("ANTHROPIC_API_KEY"):
            providers.append(ProviderConfig(
                provider_id="anthropic_default",
                provider_type="anthropic",
                display_name="Anthropic Claude (默认)",
                api_key_env="ANTHROPIC_API_KEY",
                default_model="claude-3-5-sonnet-20241022"
            ))

        # Gemini
        if os.environ.get("GEMINI_API_KEY"):
            providers.append(ProviderConfig(
                provider_id="gemini_default",
                provider_type="gemini",
                display_name="Google Gemini (默认)",
                api_key_env="GEMINI_API_KEY",
                default_model="gemini-pro"
            ))

        # Grok
        if os.environ.get("GROK_API_KEY"):
            providers.append(ProviderConfig(
                provider_id="grok_default",
                provider_type="grok",
                display_name="Grok (默认)",
                api_key_env="GROK_API_KEY",
                default_model="grok-beta"
            ))

        return LLMProvidersConfig(
            providers=providers,
            default_provider_id=providers[0].provider_id if providers else None
        )

    @classmethod
    def save_to_file(cls, config: LLMProvidersConfig, config_path: str) -> None:
        """
        Save configuration to YAML file

        Args:
            config: Configuration to save
            config_path: Path to save to
        """
        path = Path(config_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'default_provider_id': config.default_provider_id,
            'providers': [
                {
                    'provider_id': p.provider_id,
                    'provider_type': p.provider_type,
                    'display_name': p.display_name,
                    'api_key_env': p.api_key_env,
                    'default_model': p.default_model,
                    'base_url': p.base_url,
                    'enabled': p.enabled,
                    'metadata': p.metadata,
                }
                for p in config.providers
            ]
        }

        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

        logger.info(f"Saved configuration to {config_path}")


def load_llm_config() -> LLMProvidersConfig:
    """
    Load LLM provider configuration

    Priority:
    1. llm_providers.yaml in current directory
    2. config/llm_providers.yaml
    3. .config/llm_providers.yaml
    4. Default configuration from environment variables

    Returns:
        LLMProvidersConfig
    """
    # Try to load from file
    config = LLMConfigLoader.load_from_default_paths()

    if config:
        logger.info(f"Loaded configuration with {len(config.providers)} providers")
        return config

    # Fallback to default configuration
    logger.info("No configuration file found, creating default from environment variables")
    config = LLMConfigLoader.create_default_config()

    if not config.providers:
        logger.warning("No LLM providers configured and no API keys found in environment")

    return config
