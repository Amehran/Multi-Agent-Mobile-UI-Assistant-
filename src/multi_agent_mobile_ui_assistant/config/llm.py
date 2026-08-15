"""
LLM Configuration Module.

Handles LLM provider selection, initialization, and configuration.
Supports OpenAI and Ollama with extensible fallback design.
"""

import os
from typing import Literal, Optional
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.language_models.chat_models import BaseChatModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

LLMProvider = Literal["openai", "ollama"]


class LLMConfig:
    """Configuration and factory for LLM providers."""

    def __init__(
        self,
        provider: str = "ollama",
        model: Optional[str] = None,
        temperature: float = 0.7,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Initialize LLM configuration.

        Args:
            provider: LLM provider ("openai" or "ollama")
            model: Model name (defaults based on provider)
            temperature: Sampling temperature (0.0 to 1.0)
            api_key: API key for OpenAI
            base_url: Server URL for Ollama
        """
        self.provider = provider.lower()
        self.temperature = temperature

        # Default model selection
        if model is None:
            self.model = "gpt-4o-mini" if self.provider == "openai" else "llama3.2"
        else:
            self.model = model

        # OpenAI Configuration
        if self.provider == "openai":
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError(
                    "OpenAI API key required. Set OPENAI_API_KEY in your environment or .env file."
                )

        # Ollama Configuration
        if self.provider == "ollama":
            self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    def get_llm(self) -> BaseChatModel:
        """
        Instantiate and return the configured LangChain chat model.

        Returns:
            Configured BaseChatModel instance
        """
        if self.provider == "openai":
            return ChatOpenAI(
                model=self.model,
                temperature=self.temperature,
                api_key=self.api_key,
            )
        elif self.provider == "ollama":
            return ChatOllama(
                model=self.model,
                temperature=self.temperature,
                base_url=self.base_url,
            )
        else:
            raise ValueError(
                f"Unsupported provider: '{self.provider}'. Supported providers are: 'openai', 'ollama'."
            )


def create_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
) -> BaseChatModel:
    """
    Convenience function to create an LLM instance from environment or arguments.

    Args:
        provider: LLM provider name ("openai", "ollama")
        model: Model identifier
        temperature: Temperature value

    Returns:
        Configured BaseChatModel instance
    """
    if provider is None:
        provider = os.getenv("LLM_PROVIDER", "ollama")

    if model is None:
        model = os.getenv("LLM_MODEL")

    env_temp = os.getenv("LLM_TEMPERATURE")
    if env_temp is not None:
        try:
            temperature = float(env_temp)
        except ValueError:
            pass

    config = LLMConfig(
        provider=provider,
        model=model,
        temperature=temperature,
    )
    return config.get_llm()


_default_llm: Optional[BaseChatModel] = None


def get_default_llm() -> BaseChatModel:
    """
    Get or initialize the singleton default LLM instance.

    Returns:
        Default LangChain chat model
    """
    global _default_llm
    if _default_llm is None:
        _default_llm = create_llm()
    return _default_llm
